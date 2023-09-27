import copy
from datetime import datetime
import typing
import unittest
from uuid import UUID

from fastapi import BackgroundTasks

import const
import exceptions as exc
from base import enum, do, popo
from util import mock, model, security

from . import challenge


class TestAddChallengeUnderClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.challenge_id = 1

        self.data = challenge.AddChallengeInput(
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title="title",
            description="description",
            start_time=model.ServerTZDatetime(2023, 7, 29),
            end_time=model.ServerTZDatetime(2023, 7, 30),
        )
        self.data_end_before_start = copy.deepcopy(self.data)
        self.data_end_before_start.end_time = datetime(2023, 7, 28)

        self.expected_happy_flow_result = model.AddOutput(id=self.challenge_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            db_challenge.async_func('add').call_with(
                class_id=self.class_id, publicize_type=self.data.publicize_type,
                selection_type=self.data.selection_type, title=self.data.title,
                setter_id=self.account.id, description=self.data.description,
                start_time=self.data.start_time, end_time=self.data.end_time,
            ).returns(
                self.challenge_id,
            )

            result = await mock.unwrap(challenge.add_challenge_under_class)(self.class_id, self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_end_time_before_start_time(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)

            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(challenge.add_challenge_under_class)(self.class_id, self.data_end_before_start)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.add_challenge_under_class)(self.class_id, self.data)


class TestBrowseChallengeUnderClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.request_time = datetime(2023, 7, 29)

        self.class_id = 1
        self.limit = model.Limit(20)
        self.offset = model.Offset(0)
        self.filter_str = '[["content", "LIKE", "abcd"]]'
        self.sorter_str = '[]'

        self.filters = [popo.Filter(col_name='content', op=enum.FilterOperator.eq, value='abcd')]
        self.filters_before_append = copy.deepcopy(self.filters)
        self.filters.append(popo.Filter(col_name='class_id',
                                        op=enum.FilterOperator.eq,
                                        value=self.class_id))
        self.sorters = []

        self.challenges = [
            do.Challenge(
                id=1,
                class_id=1,
                publicize_type=enum.ChallengePublicizeType.start_time,
                selection_type=enum.TaskSelectionType.best,
                title='title',
                setter_id=1,
                description='desc',
                start_time=datetime(2023, 7, 29),
                end_time=datetime(2023, 7, 30),
                is_deleted=False,
            ),
            do.Challenge(
                id=2,
                class_id=1,
                publicize_type=enum.ChallengePublicizeType.start_time,
                selection_type=enum.TaskSelectionType.best,
                title='title',
                setter_id=1,
                description='desc',
                start_time=datetime(2023, 7, 29),
                end_time=datetime(2023, 7, 30),
                is_deleted=False,
            ),
        ]
        self.total_count = 2

        self.expected_happy_flow_result = challenge.BrowseChallengeUnderclassOutput(self.challenges,
                                                                                    total_count=self.total_count)

    async def test_happy_flow_class_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_system_role').call_with(
                self.account.id,
            ).returns(enum.RoleType.normal)
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.class_id,
            ).returns(enum.RoleType.manager)
            controller.mock_global_func('util.model.parse_filter').call_with(
                self.filter_str, challenge.BROWSE_CHALLENGE_COLUMNS,
            ).returns(self.filters_before_append)
            controller.mock_global_func('util.model.parse_sorter').call_with(
                self.sorter_str, challenge.BROWSE_CHALLENGE_COLUMNS,
            ).returns(self.sorters)
            db_challenge.async_func('browse').call_with(
                limit=self.limit, offset=self.offset, filters=self.filters,
                sorters=self.sorters,
                exclude_scheduled=False,
                ref_time=context.request_time,
                by_publicize_type=False,
            ).returns(
                (self.challenges, self.total_count),
            )

            result = await mock.unwrap(challenge.browse_challenge_under_class)(self.class_id, self.limit, self.offset,
                                                                               self.filter_str, self.sorter_str)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_class_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_system_role').call_with(
                self.account.id,
            ).returns(enum.RoleType.normal)
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.class_id,
            ).returns(enum.RoleType.normal)
            controller.mock_global_func('util.model.parse_filter').call_with(
                self.filter_str, challenge.BROWSE_CHALLENGE_COLUMNS,
            ).returns(self.filters_before_append)
            controller.mock_global_func('util.model.parse_sorter').call_with(
                self.sorter_str, challenge.BROWSE_CHALLENGE_COLUMNS,
            ).returns(self.sorters)
            db_challenge.async_func('browse').call_with(
                limit=self.limit, offset=self.offset, filters=self.filters,
                sorters=self.sorters,
                exclude_scheduled=True,
                ref_time=context.request_time,
                by_publicize_type=False,
            ).returns(
                (self.challenges, self.total_count),
            )

            result = await mock.unwrap(challenge.browse_challenge_under_class)(self.class_id, self.limit, self.offset,
                                                                               self.filter_str, self.sorter_str)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_no_class_role(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_system_role').call_with(
                self.account.id,
            ).returns(enum.RoleType.normal)
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.class_id,
            ).returns(None)
            controller.mock_global_func('util.model.parse_filter').call_with(
                self.filter_str, challenge.BROWSE_CHALLENGE_COLUMNS,
            ).returns(self.filters_before_append)
            controller.mock_global_func('util.model.parse_sorter').call_with(
                self.sorter_str, challenge.BROWSE_CHALLENGE_COLUMNS,
            ).returns(self.sorters)
            db_challenge.async_func('browse').call_with(
                limit=self.limit, offset=self.offset, filters=self.filters,
                sorters=self.sorters,
                exclude_scheduled=True,
                ref_time=context.request_time,
                by_publicize_type=True,
            ).returns(
                (self.challenges, self.total_count),
            )

            result = await mock.unwrap(challenge.browse_challenge_under_class)(self.class_id, self.limit, self.offset,
                                                                               self.filter_str, self.sorter_str)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_system_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_system_role').call_with(
                self.account.id,
            ).returns(enum.RoleType.guest)
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.class_id,
            ).returns(enum.RoleType.manager)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.browse_challenge_under_class)(self.class_id, self.limit, self.offset,
                                                                          self.filter_str, self.sorter_str)


class TestReadChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.request_time = datetime(2023, 7, 29, 12)
        self.request_time_before_start = datetime(2023, 7, 28, 12)

        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.challenge_unpublicized = copy.deepcopy(self.challenge)
        self.challenge_unpublicized.publicize_type = enum.ChallengePublicizeType.end_time

        self.expected_happy_flow_result = self.challenge
        self.expected_happy_flow_challenge_unpublicized_result = self.challenge_unpublicized

    async def test_happy_flow_challenge_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge.id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge.id,
            ).returns(enum.RoleType.manager)

            result = await mock.unwrap(challenge.read_challenge)(self.challenge.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_challenge_unpublicized_request_after_start(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge_unpublicized.id, ref_time=context.request_time,
            ).returns(self.challenge_unpublicized)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge_unpublicized.id,
            ).returns(enum.RoleType.manager)

            result = await mock.unwrap(challenge.read_challenge)(self.challenge_unpublicized.id)

        self.assertEqual(result, self.expected_happy_flow_challenge_unpublicized_result)

    async def test_happy_flow_challenge_unpublicized_request_before_start_class_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time_before_start)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge_unpublicized.id, ref_time=context.request_time,
            ).returns(self.challenge_unpublicized)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge_unpublicized.id,
            ).returns(enum.RoleType.manager)

            result = await mock.unwrap(challenge.read_challenge)(self.challenge_unpublicized.id)

        self.assertEqual(result, self.expected_happy_flow_challenge_unpublicized_result)

    async def test_challenge_unpublicized_request_before_start_class_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time_before_start)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge_unpublicized.id, ref_time=context.request_time,
            ).returns(self.challenge_unpublicized)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge_unpublicized.id,
            ).returns(enum.RoleType.normal)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.read_challenge)(self.challenge_unpublicized.id)

    async def test_no_system_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.read_challenge)(self.challenge_unpublicized.id)


class TestEditChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.data = challenge.EditChallengeInput(
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title="title",
            description="desc",
            start_time=model.ServerTZDatetime(2023, 7, 29),
            end_time=model.ServerTZDatetime(2023, 7, 30),
        )

    async def test_happy_flow_challenge_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            db_challenge.async_func('edit').call_with(
                challenge_id=self.challenge_id, publicize_type=self.data.publicize_type,
                selection_type=self.data.selection_type, title=self.data.title,
                description=self.data.description, start_time=self.data.start_time,
                end_time=self.data.end_time,
            ).returns(None)

            result = await mock.unwrap(challenge.edit_challenge)(self.challenge_id, self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.edit_challenge)(self.challenge_id, self.data)


class TestDeleteChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.challenge_id = 1

    async def test_happy_flow_challenge_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            db_challenge.async_func('delete').call_with(
                self.challenge_id,
            ).returns(None)

            result = await mock.unwrap(challenge.delete_challenge)(self.challenge_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.delete_challenge)(self.challenge_id)


class TestAddProblemUnderChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.problem_id = 1
        self.data = challenge.AddProblemInput(
            challenge_label="challenge",
            title="title",
            full_score=100,
            description="desc",
            io_description="io",
            source="source",
            hint="hint",
        )

        self.expected_happy_flow_result = model.AddOutput(id=self.problem_id)

    async def test_happy_flow_challenge_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            db_problem.async_func('add').call_with(
                challenge_id=self.challenge_id, challenge_label=self.data.challenge_label,
                title=self.data.title, setter_id=context.account.id, full_score=self.data.full_score,
                description=self.data.description, io_description=self.data.io_description,
                source=self.data.source, hint=self.data.hint,
            ).returns(self.problem_id)

            result = await mock.unwrap(challenge.add_problem_under_challenge)(self.challenge_id, self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.add_problem_under_challenge)(self.challenge_id, self.data)


class TestAddEssayUnderChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.essay_id = 1
        self.data = challenge.AddEssayInput(
            challenge_label="challenge",
            title="title",
            description="desc",
        )

        self.expected_happy_flow_result = model.AddOutput(id=self.essay_id)

    async def test_happy_flow_challenge_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            db_essay.async_func('add').call_with(
                challenge_id=self.challenge_id, challenge_label=self.data.challenge_label,
                title=self.data.title, setter_id=context.account.id, description=self.data.description,
            ).returns(self.essay_id)

            result = await mock.unwrap(challenge.add_essay_under_challenge)(self.challenge_id, self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.add_essay_under_challenge)(self.challenge_id, self.data)


class TestAddPeerReviewUnderChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.peer_review_id = 1

        self.data = challenge.AddPeerReviewInput(
            challenge_label="challenge",
            title="title",
            target_problem_id=1,
            description="desc",
            min_score=0,
            max_score=100,
            max_review_count=100,
        )

        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.target_problem_challenge = do.Challenge(
            id=2,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.target_problem_challenge_different_class = copy.deepcopy(self.target_problem_challenge)
        self.target_problem_challenge_different_class.class_id = 2

        self.target_problem = do.Problem(
            id=self.data.target_problem_id,
            challenge_id=self.target_problem_challenge.id,
            challenge_label="challenge",
            judge_type=enum.ProblemJudgeType.normal,
            setting_id=2,
            title="title",
            setter_id=self.account.id,
            full_score=100,
            description="desc",
            io_description="io",
            source="source",
            hint="hint",
            is_lazy_judge=False,
            is_deleted=False,
            reviser_settings=[],
        )

        self.expected_happy_flow_result = model.AddOutput(id=self.peer_review_id)

    async def test_happy_flow_challenge_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_peer_review = controller.mock_module('persistence.database.peer_review')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            db_problem.async_func('read').call_with(
                problem_id=self.data.target_problem_id,
            ).returns(self.target_problem)
            db_challenge.async_func('read').call_with(
                challenge_id=self.target_problem.challenge_id,
            ).returns(self.target_problem_challenge)
            db_challenge.async_func('read').call_with(
                self.challenge_id,
            ).returns(self.challenge)
            db_peer_review.async_func('add').call_with(
                challenge_id=self.challenge_id, challenge_label=self.data.challenge_label,
                title=self.data.title, target_problem_id=self.data.target_problem_id,
                setter_id=context.account.id, description=self.data.description,
                min_score=self.data.min_score, max_score=self.data.max_score,
                max_review_count=self.data.max_review_count,
            ).returns(self.peer_review_id)

            result = await mock.unwrap(challenge.add_peer_review_under_challenge)(self.challenge_id, self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_illegal_input(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            db_problem.async_func('read').call_with(
                problem_id=self.data.target_problem_id,
            ).returns(self.target_problem)
            db_challenge.async_func('read').call_with(
                challenge_id=self.target_problem.challenge_id,
            ).returns(self.target_problem_challenge_different_class)
            db_challenge.async_func('read').call_with(
                self.challenge_id,
            ).returns(self.challenge)

            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(challenge.add_peer_review_under_challenge)(self.challenge_id, self.data)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.add_peer_review_under_challenge)(self.challenge_id, self.data)


class TestAddTeamProjectScoreboardUnderChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.scoreboard_id = 1

        self.data = challenge.AddTeamProjectScoreboardInput(
            challenge_label="challenge",
            title="title",
            target_problem_ids=[1, 2, ],
            scoring_formula="scoring",
            baseline_team_id=1,
            rank_by_total_score=True,
            team_label_filter="team",
        )

        self.expected_happy_flow_result = model.AddOutput(id=self.scoreboard_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')
            db_scoreboard_setting_team_project = controller.mock_module(
                'persistence.database.scoreboard_setting_team_project'
            )

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            service_scoreboard.async_func('validate_formula').call_with(
                formula=self.data.scoring_formula,
            ).returns(True)
            db_scoreboard_setting_team_project.async_func('add_under_scoreboard').call_with(
                challenge_id=self.challenge_id, challenge_label=self.data.challenge_label,
                title=self.data.title, target_problem_ids=self.data.target_problem_ids,
                type_=enum.ScoreboardType.team_project, scoring_formula=self.data.scoring_formula,
                baseline_team_id=self.data.baseline_team_id, rank_by_total_score=self.data.rank_by_total_score,
                team_label_filter=self.data.team_label_filter,
            ).returns(self.scoreboard_id)

            result = await mock.unwrap(challenge.add_team_project_scoreboard_under_challenge)(self.challenge_id,
                                                                                              self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_invalid_formula(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            service_scoreboard.async_func('validate_formula').call_with(
                formula=self.data.scoring_formula,
            ).returns(False)

            with self.assertRaises(exc.InvalidFormula):
                await mock.unwrap(challenge.add_team_project_scoreboard_under_challenge)(self.challenge_id, self.data)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.add_team_project_scoreboard_under_challenge)(self.challenge_id, self.data)


class TestBrowseAllTaskUnderChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.request_time = datetime(2023, 7, 29, 12)
        self.request_time_before_start = datetime(2023, 7, 28, 12)

        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.challenge_unpublicized = copy.deepcopy(self.challenge)
        self.challenge_unpublicized.publicize_type = enum.ChallengePublicizeType.end_time

        self.problems = [
            do.Problem(
                id=1,
                challenge_id=1,
                challenge_label='label',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            ),
            do.Problem(
                id=2,
                challenge_id=1,
                challenge_label='label2',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title2',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            ),
        ]
        self.peer_reviews = [
            do.PeerReview(
                id=1,
                challenge_id=1,
                challenge_label='test',
                title='test',
                target_problem_id=1,
                setter_id=1,
                description='test_only',
                min_score=1,
                max_score=10,
                max_review_count=10,
                is_deleted=False,
            ),
            do.PeerReview(
                id=2,
                challenge_id=1,
                challenge_label='test',
                title='test',
                target_problem_id=1,
                setter_id=1,
                description='test_only',
                min_score=1,
                max_score=10,
                max_review_count=10,
                is_deleted=False,
            ),
        ]
        self.essays = [
            do.Essay(
                id=1,
                challenge_id=self.challenge.id,
                challenge_label="challenge",
                title="title",
                setter_id=self.account.id,
                description="desc",
                is_deleted=False,
            ),
            do.Essay(
                id=2,
                challenge_id=self.challenge.id,
                challenge_label="challenge",
                title="title",
                setter_id=self.account.id,
                description="desc",
                is_deleted=False,
            )
        ]
        self.scoreboard = [
            do.Scoreboard(
                id=1,
                challenge_id=1,
                challenge_label='label',
                title='title',
                target_problem_ids=[1, 2],
                is_deleted=False,
                type=enum.ScoreboardType.team_project,
                setting_id=1,
            ),
            do.Scoreboard(
                id=2,
                challenge_id=1,
                challenge_label='label',
                title='title',
                target_problem_ids=[1, 2],
                is_deleted=False,
                type=enum.ScoreboardType.team_project,
                setting_id=1,
            ),
        ]

        self.expected_happy_flow_result = challenge.BrowseTaskOutput(
            problem=self.problems,
            peer_review=self.peer_reviews,
            essay=self.essays,
            scoreboard=self.scoreboard,
        )
        self.expected_no_class_role_result = challenge.BrowseTaskOutput(
            problem=self.problems,
            peer_review=[],
            essay=[],
            scoreboard=[],
        )

    async def test_happy_flow_class_manager_before_start_time_system_guest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time_before_start)

            service_rbac = controller.mock_module('service.rbac')
            service_task = controller.mock_module('service.task')
            db_challenge = controller.mock_module('persistence.database.challenge')

            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge.id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge.id,
            ).returns(enum.RoleType.manager)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)
            service_task.async_func('browse').call_with(self.challenge.id).returns(
                (self.problems, self.peer_reviews, self.essays, self.scoreboard),
            )

            result = await mock.unwrap(challenge.browse_all_task_under_challenge)(self.challenge.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_class_guest_after_start_time(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            service_task = controller.mock_module('service.task')
            db_challenge = controller.mock_module('persistence.database.challenge')

            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge.id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge.id,
            ).returns(enum.RoleType.guest)
            service_task.async_func('browse').call_with(self.challenge.id).returns(
                (self.problems, self.peer_reviews, self.essays, self.scoreboard),
            )

            result = await mock.unwrap(challenge.browse_all_task_under_challenge)(self.challenge.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_class_guest_before_start_time_system_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time_before_start)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge.id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge.id,
            ).returns(enum.RoleType.guest)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.browse_all_task_under_challenge)(self.challenge.id)

    async def test_class_guest_before_start_time_system_guest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time_before_start)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge.id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge.id,
            ).returns(enum.RoleType.guest)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.browse_all_task_under_challenge)(self.challenge.id)

    async def test_no_class_role_system_normal_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            service_task = controller.mock_module('service.task')
            db_challenge = controller.mock_module('persistence.database.challenge')

            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge.id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge.id,
            ).returns(None)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_task.async_func('browse').call_with(self.challenge.id).returns(
                (self.problems, self.peer_reviews, self.essays, self.scoreboard),
            )

            result = await mock.unwrap(challenge.browse_all_task_under_challenge)(self.challenge.id)

        self.assertEqual(result, self.expected_no_class_role_result)

    async def test_no_class_role_system_normal_unpublicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge_unpublicized.id, ref_time=context.request_time,
            ).returns(self.challenge_unpublicized)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge_unpublicized.id,
            ).returns(None)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.browse_all_task_under_challenge)(self.challenge.id)

    async def test_no_class_role_system_guest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_challenge = controller.mock_module('persistence.database.challenge')

            db_challenge.async_func('read').call_with(
                challenge_id=self.challenge.id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, challenge_id=self.challenge.id,
            ).returns(None)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.browse_all_task_under_challenge)(self.challenge.id)


class TestBrowseAllTaskStatusUnderChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.results = [
            (
                do.Problem(
                    id=1,
                    challenge_id=1,
                    challenge_label='label',
                    judge_type=enum.ProblemJudgeType.normal,
                    setting_id=None,
                    title='title',
                    setter_id=1,
                    full_score=100,
                    description='desc',
                    io_description='io_desc',
                    source='src',
                    hint='hint',
                    is_lazy_judge=False,
                    is_deleted=False,
                    reviser_settings=[],
                ),
                do.Challenge(
                    id=1,
                    class_id=1,
                    publicize_type=enum.ChallengePublicizeType.start_time,
                    selection_type=enum.TaskSelectionType.best,
                    title='title',
                    setter_id=1,
                    description='desc',
                    start_time=datetime(2023, 7, 29),
                    end_time=datetime(2023, 7, 30),
                    is_deleted=False,
                )
            ),
            (
                do.Problem(
                    id=2,
                    challenge_id=1,
                    challenge_label='label',
                    judge_type=enum.ProblemJudgeType.normal,
                    setting_id=None,
                    title='title',
                    setter_id=1,
                    full_score=100,
                    description='desc',
                    io_description='io_desc',
                    source='src',
                    hint='hint',
                    is_lazy_judge=False,
                    is_deleted=False,
                    reviser_settings=[],
                ),
                do.Challenge(
                    id=2,
                    class_id=1,
                    publicize_type=enum.ChallengePublicizeType.start_time,
                    selection_type=enum.TaskSelectionType.best,
                    title='title',
                    setter_id=1,
                    description='desc',
                    start_time=datetime(2023, 7, 29),
                    end_time=datetime(2023, 7, 30),
                    is_deleted=False,
                )
            ),
        ]

        self.expected_happy_flow_result = [
            challenge.ReadStatusOutput(
                problem=[
                    challenge.ReadProblemStatusOutput(problem_id=1, submission_id=1),
                    challenge.ReadProblemStatusOutput(problem_id=2, submission_id=2),
                ],
            )
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_task = controller.mock_module('service.task')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.guest,
                challenge_id=self.challenge_id,
            ).returns(True)
            service_task.async_func('browse_status').call_with(
                self.challenge_id, account_id=context.account.id,
            ).returns(self.results)

            result = await mock.unwrap(challenge.browse_all_task_status_under_challenge)(self.challenge_id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.guest,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.browse_all_task_status_under_challenge)(self.challenge_id)


class TestGetChallengeStatistics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.result = [
            ("", 1, 1, 1, ), ("", 2, 2, 2, ),
        ]

        self.expected_happy_flow_result = challenge.GetChallengeStatOutput(
            tasks=[
                challenge.ProblemStatOutput(
                    task_label="",
                    solved_member_count=1,
                    submission_count=1,
                    member_count=1,
                ),
                challenge.ProblemStatOutput(
                    task_label="",
                    solved_member_count=2,
                    submission_count=2,
                    member_count=2,
                ),
            ]
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_statistics = controller.mock_module('service.statistics')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            service_statistics.async_func('get_challenge_statistics').call_with(
                challenge_id=self.challenge_id,
            ).returns(self.result)

            result = await mock.unwrap(challenge.get_challenge_statistics)(self.challenge_id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.get_challenge_statistics)(self.challenge_id)


class TestGetMemberSubmissionStatistics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.results = [
            (1,
             [
                 (1, do.Judgment(
                     id=1,
                     submission_id=1,
                     verdict=enum.VerdictType.accepted,
                     total_time=100,
                     max_memory=100,
                     score=10,
                     error_message=None,
                     judge_time=datetime(2023, 7, 29, 12),
                 )),
                 (2, do.Judgment(
                     id=2,
                     submission_id=1,
                     verdict=enum.VerdictType.accepted,
                     total_time=100,
                     max_memory=100,
                     score=10,
                     error_message=None,
                     judge_time=datetime(2023, 7, 29, 12),
                 )),
                ],
                [
                do.EssaySubmission(
                    id=1,
                    account_id=self.account.id,
                    essay_id=1,
                    content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                    filename='test1',
                    submit_time=datetime(2023, 7, 29, 12),
                ),
                do.EssaySubmission(
                    id=2,
                    account_id=self.account.id,
                    essay_id=1,
                    content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                    filename='test1',
                    submit_time=datetime(2023, 7, 29, 12),
                ),
                ]),
            (2,
             [
                 (1, do.Judgment(
                     id=1,
                     submission_id=1,
                     verdict=enum.VerdictType.accepted,
                     total_time=100,
                     max_memory=100,
                     score=10,
                     error_message=None,
                     judge_time=datetime(2023, 7, 29, 12),
                 )),
                 (2, do.Judgment(
                     id=2,
                     submission_id=1,
                     verdict=enum.VerdictType.accepted,
                     total_time=100,
                     max_memory=100,
                     score=10,
                     error_message=None,
                     judge_time=datetime(2023, 7, 29, 12),
                 )),
             ],
             [
                 do.EssaySubmission(
                     id=1,
                     account_id=self.account.id,
                     essay_id=1,
                     content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                     filename='test1',
                     submit_time=datetime(2023, 7, 29, 12),
                 ),
                 do.EssaySubmission(
                     id=2,
                     account_id=self.account.id,
                     essay_id=1,
                     content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                     filename='test1',
                     submit_time=datetime(2023, 7, 29, 12),
                 ),
             ]),
        ]
        self.member_submission_stat = challenge.GetMemberSubmissionStatOutput(
            member=[
                challenge.MemberSubmissionStatOutput(
                    id=1,
                    problem_scores=[
                        challenge.ProblemScores(
                            problem_id=1,
                            judgment=do.Judgment(
                                id=1,
                                submission_id=1,
                                verdict=enum.VerdictType.accepted,
                                total_time=100,
                                max_memory=100,
                                score=10,
                                error_message=None,
                                judge_time=datetime(2023, 7, 29, 12),
                            ),
                        ),
                        challenge.ProblemScores(
                            problem_id=2,
                            judgment=do.Judgment(
                                id=2,
                                submission_id=1,
                                verdict=enum.VerdictType.accepted,
                                total_time=100,
                                max_memory=100,
                                score=10,
                                error_message=None,
                                judge_time=datetime(2023, 7, 29, 12),
                            ),
                        ),
                    ],
                    essay_submissions=[
                        do.EssaySubmission(
                            id=1,
                            account_id=self.account.id,
                            essay_id=1,
                            content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                            filename='test1',
                            submit_time=datetime(2023, 7, 29, 12),
                        ),
                        do.EssaySubmission(
                            id=2,
                            account_id=self.account.id,
                            essay_id=1,
                            content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                            filename='test1',
                            submit_time=datetime(2023, 7, 29, 12),
                        ),
                    ],
                ),
                challenge.MemberSubmissionStatOutput(
                    id=2,
                    problem_scores=[
                        challenge.ProblemScores(
                            problem_id=1,
                            judgment=do.Judgment(
                                id=1,
                                submission_id=1,
                                verdict=enum.VerdictType.accepted,
                                total_time=100,
                                max_memory=100,
                                score=10,
                                error_message=None,
                                judge_time=datetime(2023, 7, 29, 12),
                            ),
                        ),
                        challenge.ProblemScores(
                            problem_id=2,
                            judgment=do.Judgment(
                                id=2,
                                submission_id=1,
                                verdict=enum.VerdictType.accepted,
                                total_time=100,
                                max_memory=100,
                                score=10,
                                error_message=None,
                                judge_time=datetime(2023, 7, 29, 12),
                            ),
                        ),
                    ],
                    essay_submissions=[
                        do.EssaySubmission(
                            id=1,
                            account_id=self.account.id,
                            essay_id=1,
                            content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                            filename='test1',
                            submit_time=datetime(2023, 7, 29, 12),
                        ),
                        do.EssaySubmission(
                            id=2,
                            account_id=self.account.id,
                            essay_id=1,
                            content_file_uuid=do.UUID('{12345678-1234-5678-1234-567812345678}'),
                            filename='test1',
                            submit_time=datetime(2023, 7, 29, 12),
                        ),
                    ],
                ),
            ],
        )

        self.expected_happy_flow_result = challenge.GetMemberSubmissionStatisticsOutput(
            data=self.member_submission_stat, total_count=self.results.__len__(),
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_statistics = controller.mock_module('service.statistics')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            service_statistics.async_func('get_member_submission_statistics').call_with(
                challenge_id=self.challenge_id,
            ).returns(self.results)

            result = await mock.unwrap(challenge.get_member_submission_statistics)(self.challenge_id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.get_member_submission_statistics)(self.challenge_id)


class TestDownloadAllSubmissions(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='username')
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.background_tasks = BackgroundTasks()
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'title.zip'
        self.file_url = 'file_url'
        self.subject = f'[PDOGS] All submissions for {self.challenge.title}'

        self.account = do.Account(
            id=1,
            username="username",
            nickname="nickname",
            real_name="real",
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.account_no_alternative_email = copy.deepcopy(self.account)
        self.account_no_alternative_email.alternative_email = None

        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='1',
            email="email",
            is_default=True,
        )
        self.student_card_no_email = copy.deepcopy(self.student_card)
        self.student_card_no_email.email = None

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                           as_attachment=True,
                                                                           background_tasks=self.background_tasks)

            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_downloader.async_func('all_submissions').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                filename=self.filename, as_attachment=True,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account, self.student_card),
            )

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)
            email_notification.async_func('send_file_download_url').call_with(
                to=self.account.alternative_email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_happy_flow_no_student_card_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                           as_attachment=True,
                                                                           background_tasks=self.background_tasks)

            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_downloader.async_func('all_submissions').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                filename=self.filename, as_attachment=True,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account, self.student_card_no_email),
            )

            email_notification.async_func('send_file_download_url').call_with(
                to=self.account.alternative_email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_happy_flow_no_account_alternative_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                           as_attachment=True,
                                                                           background_tasks=self.background_tasks)

            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_downloader.async_func('all_submissions').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                filename=self.filename, as_attachment=True,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account_no_alternative_email, self.student_card),
            )

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                      as_attachment=True,
                                                                      background_tasks=self.background_tasks)


class TestDownloadAllAssistingData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='username')
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.background_tasks = BackgroundTasks()
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'title.zip'
        self.file_url = 'file_url'
        self.subject = f'[PDOGS] All submissions for {self.challenge.title}'

        self.account = do.Account(
            id=1,
            username="username",
            nickname="nickname",
            real_name="real",
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.account_no_alternative_email = copy.deepcopy(self.account)
        self.account_no_alternative_email.alternative_email = None

        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='1',
            email="email",
            is_default=True,
        )
        self.student_card_no_email = copy.deepcopy(self.student_card)
        self.student_card_no_email.email = None

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                           as_attachment=True,
                                                                           background_tasks=self.background_tasks)

            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_downloader.async_func('all_submissions').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                filename=self.filename, as_attachment=True,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account, self.student_card),
            )

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)
            email_notification.async_func('send_file_download_url').call_with(
                to=self.account.alternative_email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_happy_flow_no_student_card_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                           as_attachment=True,
                                                                           background_tasks=self.background_tasks)

            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_downloader.async_func('all_submissions').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                filename=self.filename, as_attachment=True,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account, self.student_card_no_email),
            )

            email_notification.async_func('send_file_download_url').call_with(
                to=self.account.alternative_email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_happy_flow_no_account_alternative_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                           as_attachment=True,
                                                                           background_tasks=self.background_tasks)

            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_downloader.async_func('all_submissions').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                filename=self.filename, as_attachment=True,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account_no_alternative_email, self.student_card),
            )

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email,
                file_url=self.file_url, subject=self.subject,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.download_all_submissions)(challenge_id=self.challenge.id,
                                                                      as_attachment=True,
                                                                      background_tasks=self.background_tasks)


class TestDownloadAllPlagiarismReports(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='username')

        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.problems = [
            do.Problem(
                id=1,
                challenge_id=1,
                challenge_label='label',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            ),
            do.Problem(
                id=2,
                challenge_id=1,
                challenge_label='label',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            ),
        ]
        self.background_tasks = BackgroundTasks()
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'title_plagiarism_report.zip'
        self.file_url = 'file_url'

        self.problem_title = self.challenge.title + ' label'
        self.report_url = "report"
        self.msg = f'Plagiarism report for {self.problem_title}: {self.report_url}'

        self.account = do.Account(
            id=1,
            username="username",
            nickname="nickname",
            real_name="real",
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.account_no_alternative_email = copy.deepcopy(self.account)
        self.account_no_alternative_email.alternative_email = None

        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='1',
            email="email",
            is_default=True,
        )
        self.student_card_no_email = copy.deepcopy(self.student_card)
        self.student_card_no_email.email = None

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_moss = controller.mock_module('service.moss')
            service_downloader = controller.mock_module('service.downloader')
            util_background_task = controller.mock_module('util.background_task')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_problem = controller.mock_module('persistence.database.problem')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_plagiarism_reports)(
                challenge_id=self.challenge.id, as_attachment=True,
                background_tasks=self.background_tasks,
            )

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account, self.student_card),
            )
            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            db_problem.async_func('browse_by_challenge').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.problems)

            for problem in self.problems:
                service_moss.async_func('check_all_submissions_moss').call_with(
                    title=self.problem_title,
                    challenge=self.challenge, problem=problem,
                ).returns(self.report_url)
                email_notification.async_func('send').call_with(
                    to=self.student_card.email,
                    subject=f'[PDOGS] Plagiarism report for {self.problem_title}',
                    msg=self.msg,
                ).returns(None)
                email_notification.async_func('send').call_with(
                    to=self.account.alternative_email,
                    subject=f'[PDOGS] Plagiarism report for {self.problem_title}',
                    msg=self.msg,
                ).returns(None)
                service_downloader.async_func('moss_report').call_with(
                    report_url=self.report_url,
                ).returns(self.s3_file)
                s3_tools.async_func('sign_url').call_with(
                    bucket=self.s3_file.bucket, key=self.s3_file.key,
                    expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                    filename=self.filename, as_attachment=True,
                ).returns(self.file_url)
                email_notification.async_func('send_file_download_url').call_with(
                    to=self.student_card.email, file_url=self.file_url,
                    subject=f'[PDOGS] Plagiarism report file for {self.problem_title}',
                ).returns(None)
                email_notification.async_func('send_file_download_url').call_with(
                    to=self.account.alternative_email, file_url=self.file_url,
                    subject=f'[PDOGS] Plagiarism report file for {self.problem_title}',
                ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_happy_flow_no_student_card_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_moss = controller.mock_module('service.moss')
            service_downloader = controller.mock_module('service.downloader')
            util_background_task = controller.mock_module('util.background_task')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_problem = controller.mock_module('persistence.database.problem')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_plagiarism_reports)(
                challenge_id=self.challenge.id, as_attachment=True,
                background_tasks=self.background_tasks,
            )

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account, self.student_card_no_email),
            )
            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            db_problem.async_func('browse_by_challenge').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.problems)

            for problem in self.problems:
                service_moss.async_func('check_all_submissions_moss').call_with(
                    title=self.problem_title,
                    challenge=self.challenge, problem=problem,
                ).returns(self.report_url)
                email_notification.async_func('send').call_with(
                    to=self.account.alternative_email,
                    subject=f'[PDOGS] Plagiarism report for {self.problem_title}',
                    msg=self.msg,
                ).returns(None)
                service_downloader.async_func('moss_report').call_with(
                    report_url=self.report_url,
                ).returns(self.s3_file)
                s3_tools.async_func('sign_url').call_with(
                    bucket=self.s3_file.bucket, key=self.s3_file.key,
                    expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                    filename=self.filename, as_attachment=True,
                ).returns(self.file_url)
                email_notification.async_func('send_file_download_url').call_with(
                    to=self.account.alternative_email, file_url=self.file_url,
                    subject=f'[PDOGS] Plagiarism report file for {self.problem_title}',
                ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_happy_flow_no_account_alternative_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_moss = controller.mock_module('service.moss')
            service_downloader = controller.mock_module('service.downloader')
            util_background_task = controller.mock_module('util.background_task')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_problem = controller.mock_module('persistence.database.problem')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(challenge.download_all_plagiarism_reports)(
                challenge_id=self.challenge.id, as_attachment=True,
                background_tasks=self.background_tasks,
            )

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account_no_alternative_email, self.student_card),
            )
            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            db_problem.async_func('browse_by_challenge').call_with(
                challenge_id=self.challenge.id,
            ).returns(self.problems)

            for problem in self.problems:
                service_moss.async_func('check_all_submissions_moss').call_with(
                    title=self.problem_title,
                    challenge=self.challenge, problem=problem,
                ).returns(self.report_url)
                email_notification.async_func('send').call_with(
                    to=self.student_card.email,
                    subject=f'[PDOGS] Plagiarism report for {self.problem_title}',
                    msg=self.msg,
                ).returns(None)
                service_downloader.async_func('moss_report').call_with(
                    report_url=self.report_url,
                ).returns(self.s3_file)
                s3_tools.async_func('sign_url').call_with(
                    bucket=self.s3_file.bucket, key=self.s3_file.key,
                    expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                    filename=self.filename, as_attachment=True,
                ).returns(self.file_url)
                email_notification.async_func('send_file_download_url').call_with(
                    to=self.student_card.email, file_url=self.file_url,
                    subject=f'[PDOGS] Plagiarism report file for {self.problem_title}',
                ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.download_all_plagiarism_reports)(
                    challenge_id=self.challenge.id, as_attachment=True,
                    background_tasks=self.background_tasks,
                )


class TestAddTeamContestScoreboardUnderChallenge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.challenge_id = 1
        self.scoreboard_id = 1

        self.data = challenge.AddTeamContestScoreboardInput(
            challenge_label="label",
            title="title",
            target_problem_ids=[1, 2, ],
            penalty_formula="formula",
            team_label_filter="filter",
        )

        self.expected_happy_flow_result = model.AddOutput(id=self.scoreboard_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')
            db_scoreboard_setting_team_contest = controller.mock_module(
                'persistence.database.scoreboard_setting_team_contest'
            )

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            service_scoreboard.func('validate_penalty_formula').call_with(
                formula=self.data.penalty_formula,
            ).returns(True)
            db_scoreboard_setting_team_contest.async_func('add_under_scoreboard').call_with(
                challenge_id=self.challenge_id, challenge_label=self.data.challenge_label,
                title=self.data.title, target_problem_ids=self.data.target_problem_ids,
                penalty_formula=self.data.penalty_formula, team_label_filter=self.data.team_label_filter,
            ).returns(self.scoreboard_id)

            result = await mock.unwrap(challenge.add_team_contest_scoreboard_under_challenge)(self.challenge_id,
                                                                                              self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_invalid_formula(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(True)
            service_scoreboard.func('validate_penalty_formula').call_with(
                formula=self.data.penalty_formula,
            ).returns(False)

            with self.assertRaises(exc.InvalidFormula):
                await mock.unwrap(challenge.add_team_contest_scoreboard_under_challenge)(self.challenge_id, self.data)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                challenge_id=self.challenge_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(challenge.add_team_contest_scoreboard_under_challenge)(self.challenge_id, self.data)
