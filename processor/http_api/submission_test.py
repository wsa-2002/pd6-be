import copy
from datetime import datetime
import typing
import unittest
from uuid import UUID

from fastapi import UploadFile, BackgroundTasks

import exceptions as exc
from base import enum, do, popo
from util import mock, model, security

from . import submission


class TestBrowseAllSubmissionLanguage(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.all_submission_language = [
            do.SubmissionLanguage(
                id=1,
                name="name",
                version="version",
                is_disabled=False,
            ),
            do.SubmissionLanguage(
                id=2,
                name="name",
                version="version",
                is_disabled=False,
            ),
        ]
        self.expected_happy_flow_result = self.all_submission_language

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_institute.async_func('browse_language').call_with().returns(
                self.all_submission_language,
            )

            result = await mock.unwrap(submission.browse_all_submission_language)()

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.browse_all_submission_language)()


class TestAddSubmissionLanguage(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.submission_language = do.SubmissionLanguage(
            id=1,
            name="name",
            version="version",
            is_disabled=False,
        )
        self.data = submission.AddSubmissionLanguageInput(
            name=self.submission_language.name,
            version=self.submission_language.version,
            queue_name="queue",
            is_disabled=self.submission_language.is_disabled,
        )

        self.expected_happy_flow_result = model.AddOutput(id=self.submission_language.id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.manager,
            ).returns(True)
            db_submission.async_func('add_language').call_with(
                name=self.data.name, version=self.data.version,
                queue_name=self.data.queue_name, is_disabled=self.data.is_disabled,
            ).returns(
                self.submission_language.id,
            )

            result = await mock.unwrap(submission.add_submission_language)(self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.add_submission_language)(self.data)


class TestEditSubmissionLanguage(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.language = do.SubmissionLanguage(
            id=1,
            name="name",
            version="version",
            is_disabled=False,
        )
        self.data = submission.EditSubmissionLanguageInput(
            name="name_edit",
            version="version_edit",
            is_disabled=False,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.manager,
            ).returns(True)
            db_submission.async_func('edit_language').call_with(
                self.language.id,
                name=self.data.name, version=self.data.version, is_disabled=self.data.is_disabled,
            ).returns(None)

            result = await mock.unwrap(submission.edit_submission_language)(self.language.id, self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.edit_submission_language)(self.language.id, self.data)


class TestSubmit(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.background_tasks = BackgroundTasks()
        self.class_member_manager = do.ClassMember(
            member_id=self.account.id,
            class_id=1,
            role=enum.RoleType.manager,
        )
        self.class_member_normal = do.ClassMember(
            member_id=self.account.id,
            class_id=1,
            role=enum.RoleType.normal,
        )

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

        self.problem = do.Problem(
            id=1,
            challenge_id=self.challenge.id,
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
        )

        self.language = do.SubmissionLanguage(
            id=1,
            name="name",
            version="version",
            is_disabled=False,
        )
        self.language_disabled = copy.deepcopy(self.language)
        self.language_disabled.is_disabled = True

        self.submission = do.Submission(
            id=1,
            account_id=self.account.id,
            problem_id=self.problem.id,
            language_id=self.language.id,
            content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            content_length=0,
            filename="filename",
            submit_time=self.request_time,
        )

        self.content_file = UploadFile(filename="filename")
        self.file_length = 0

        self.expected_happy_flow_result = model.AddOutput(id=self.submission.id)
        self.expected_class_normal_after_start_publicized_result = model.AddOutput(id=self.submission.id)
        self.expected_class_normal_after_start_unpublicized_result = model.AddOutput(id=self.submission.id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            service_judge = controller.mock_module('service.judge')
            service_submission = controller.mock_module('service.submission')
            util_background_task = controller.mock_module('util.background_task')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_problem.async_func('read').call_with(self.problem.id).returns(
                self.problem,
            )
            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.challenge.class_id,
            ).returns(self.class_member_manager.role)
            db_submission.async_func('read_language').call_with(self.language.id).returns(
                self.language,
            )
            service_submission.async_func('submit').call_with(
                file=mock.AnyInstanceOf(type(self.content_file.file)), filename=self.content_file.filename,
                account_id=self.account.id, problem_id=self.problem.id,
                file_length=self.file_length, language_id=self.language.id,
                submit_time=self.request_time,
            ).returns(self.submission.id)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(submission.submit)(self.problem.id, self.language.id,
                                                          self.background_tasks, self.content_file)

            service_judge.async_func('judge_submission').call_with(
                self.submission.id,
            ).returns(None)

            await todo_async_task()

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_language_disabled(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_problem.async_func('read').call_with(self.problem.id).returns(
                self.problem,
            )
            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.challenge.class_id,
            ).returns(self.class_member_manager.role)
            db_submission.async_func('read_language').call_with(self.language.id).returns(
                self.language_disabled,
            )

            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(submission.submit)(self.problem.id, self.language_disabled.id,
                                                     self.background_tasks, self.content_file)

    async def test_class_normal_after_start_publicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            service_judge = controller.mock_module('service.judge')
            service_submission = controller.mock_module('service.submission')
            util_background_task = controller.mock_module('util.background_task')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_problem.async_func('read').call_with(self.problem.id).returns(
                self.problem,
            )
            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.challenge.class_id,
            ).returns(self.class_member_normal.role)
            db_submission.async_func('read_language').call_with(self.language.id).returns(
                self.language,
            )
            service_submission.async_func('submit').call_with(
                file=mock.AnyInstanceOf(type(self.content_file.file)), filename=self.content_file.filename,
                account_id=self.account.id, problem_id=self.problem.id,
                file_length=self.file_length, language_id=self.language.id,
                submit_time=self.request_time,
            ).returns(self.submission.id)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(submission.submit)(self.problem.id, self.language.id,
                                                          self.background_tasks, self.content_file)

            service_judge.async_func('judge_submission').call_with(
                self.submission.id,
            ).returns(None)

            await todo_async_task()

        self.assertEqual(result, self.expected_class_normal_after_start_publicized_result)

    async def test_class_normal_after_start_unpublicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            service_judge = controller.mock_module('service.judge')
            service_submission = controller.mock_module('service.submission')
            util_background_task = controller.mock_module('util.background_task')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_problem.async_func('read').call_with(self.problem.id).returns(
                self.problem,
            )
            db_challenge.async_func('read').call_with(self.challenge_unpublicized.id).returns(
                self.challenge_unpublicized,
            )
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.challenge_unpublicized.class_id,
            ).returns(self.class_member_normal.role)
            db_submission.async_func('read_language').call_with(self.language.id).returns(
                self.language,
            )
            service_submission.async_func('submit').call_with(
                file=mock.AnyInstanceOf(type(self.content_file.file)), filename=self.content_file.filename,
                account_id=self.account.id, problem_id=self.problem.id,
                file_length=self.file_length, language_id=self.language.id,
                submit_time=self.request_time,
            ).returns(self.submission.id)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(submission.submit)(self.problem.id, self.language.id,
                                                          self.background_tasks, self.content_file)

            service_judge.async_func('judge_submission').call_with(
                self.submission.id,
            ).returns(None)

            await todo_async_task()
        self.assertEqual(result, self.expected_class_normal_after_start_unpublicized_result)

    async def test_class_normal_before_start_unpublicized(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time_before_start)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_problem.async_func('read').call_with(self.problem.id).returns(
                self.problem,
            )
            db_challenge.async_func('read').call_with(self.challenge.id).returns(
                self.challenge,
            )
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, class_id=self.challenge.class_id,
            ).returns(self.class_member_normal.role)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.submit)(self.problem.id, self.language_disabled.id,
                                                     self.background_tasks, self.content_file)

    async def test_no_system_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.submit)(self.problem.id, self.language.id,
                                                     self.background_tasks, self.content_file)


class TestBrowseSubmission(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.account_other = security.AuthedAccount(id=2, cached_username='other')

        self.limit = model.Limit(20)
        self.offset = model.Offset(0)
        self.filter = '[["content", "LIKE", "abcd"]]'
        self.sort = None

        self.BROWSE_SUBMISSION_COLUMNS = submission.BROWSE_SUBMISSION_COLUMNS
        self.filters = [popo.Filter(col_name='content', op=enum.FilterOperator.like, value='abcd')]
        self.filters_before_append = copy.deepcopy(self.filters)
        self.filters.append(popo.Filter(col_name='account_id',
                                        op=enum.FilterOperator.eq,
                                        value=self.account.id))
        self.sorters = []

        self.submissions = [
            do.Submission(
                id=1,
                account_id=self.account.id,
                problem_id=1,
                language_id=1,
                content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                content_length=0,
                filename="filename",
                submit_time=datetime(2023, 7, 29, 12),
            ),
            do.Submission(
                id=2,
                account_id=2,
                problem_id=2,
                language_id=2,
                content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                content_length=0,
                filename="filename",
                submit_time=datetime(2023, 7, 29, 12),
            ),
        ]
        self.total_count = len(self.submissions)

        self.expected_happy_flow_result = submission.BrowseSubmissionOutput(self.submissions,
                                                                            total_count=self.total_count)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            db_submission = controller.mock_module('persistence.database.submission')
            util_model = controller.mock_module('util.model')

            util_model.func('parse_filter').call_with(
                self.filter, self.BROWSE_SUBMISSION_COLUMNS,
            ).returns(self.filters_before_append)
            util_model.func('parse_sorter').call_with(
                self.sort, self.BROWSE_SUBMISSION_COLUMNS,
            ).returns(self.sorters)

            db_submission.async_func('browse').call_with(
                limit=self.limit, offset=self.offset,
                filters=self.filters, sorters=self.sorters,
            ).returns(
                (self.submissions, self.total_count),
            )

            result = await mock.unwrap(submission.browse_submission)(self.account.id, self.limit,
                                                                     self.offset, self.filter, self.sort)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Context() as context,
        ):
            context.set_account(self.account_other)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.browse_submission)(self.account.id, self.limit,
                                                                self.offset, self.filter, self.sort)


class TestBatchGetSubmissionJudgment(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.submission_ids_json = None
        self.submission_ids = [1, 2, ]
        self.submission_ids_empty = []

        self.judgments = [
            do.Judgment(
                id=1,
                submission_id=1,
                verdict=enum.VerdictType.accepted,
                total_time=1,
                max_memory=1,
                score=100,
                error_message="",
                judge_time=datetime(2023, 7, 29, 12),
            ),
            do.Judgment(
                id=2,
                submission_id=2,
                verdict=enum.VerdictType.accepted,
                total_time=1,
                max_memory=1,
                score=100,
                error_message="",
                judge_time=datetime(2023, 7, 29, 12),
            ),
        ]

        self.expected_happy_flow_result = self.judgments
        self.expected_no_submission_ids_result = []

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            db_judgment = controller.mock_module('persistence.database.judgment')
            service_rbac = controller.mock_module('service.rbac')

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                list[int], self.submission_ids_json,
            ).returns(self.submission_ids)
            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_judgment.async_func('browse_latest_with_submission_ids').call_with(
                submission_ids=self.submission_ids,
            ).returns(self.judgments)

            result = await mock.unwrap(submission.batch_get_submission_judgment)(self.submission_ids_json)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            service_rbac = controller.mock_module('service.rbac')

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                list[int], self.submission_ids_json,
            ).returns(self.submission_ids)
            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.batch_get_submission_judgment)(self.submission_ids_json)

    async def test_no_submission_ids(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                list[int], self.submission_ids_json,
            ).returns(self.submission_ids_empty)

            result = await mock.unwrap(submission.batch_get_submission_judgment)(self.submission_ids_json)

        self.assertEqual(result, self.expected_no_submission_ids_result)


class TestReadSubmission(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.account_class_manager = security.AuthedAccount(id=2, cached_username='class_manager')

        self.submission = do.Submission(
            id=1,
            account_id=self.account.id,
            problem_id=1,
            language_id=1,
            content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            content_length=0,
            filename="filename",
            submit_time=datetime(2023, 7, 29, 12),
        )

        self.expected_happy_flow_result = self.submission

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            db_submission = controller.mock_module('persistence.database.submission')

            db_submission.async_func('read').call_with(
                submission_id=self.submission.id,
            ).returns(self.submission)

            result = await mock.unwrap(submission.read_submission)(self.submission.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_class_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account_class_manager)

            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_submission.async_func('read').call_with(
                submission_id=self.submission.id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                self.account_class_manager.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(True)

            result = await mock.unwrap(submission.read_submission)(self.submission.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account_class_manager)

            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_submission.async_func('read').call_with(
                submission_id=self.submission.id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                self.account_class_manager.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.read_submission)(self.submission.id)


class TestBrowseAllSubmissionJudgment(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.submission = do.Submission(
            id=1,
            account_id=self.account.id,
            problem_id=1,
            language_id=1,
            content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            content_length=0,
            filename="filename",
            submit_time=datetime(2023, 7, 29, 12),
        )
        self.judgments = [
            do.Judgment(
                id=1,
                submission_id=self.submission.id,
                verdict=enum.VerdictType.accepted,
                total_time=1,
                max_memory=1,
                score=100,
                error_message="",
                judge_time=datetime(2023, 7, 29, 12),
            ),
            do.Judgment(
                id=2,
                submission_id=self.submission.id,
                verdict=enum.VerdictType.accepted,
                total_time=1,
                max_memory=1,
                score=100,
                error_message="",
                judge_time=datetime(2023, 7, 29, 12),
            ),
        ]

        self.expected_happy_flow_result = self.judgments

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_judgment = controller.mock_module('persistence.database.judgment')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(True)
            db_judgment.async_func('browse').call_with(
                submission_id=self.submission.id,
            ).returns(self.judgments)

            result = await mock.unwrap(submission.browse_all_submission_judgment)(self.submission.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.browse_all_submission_judgment)(self.submission.id)


class TestReadSubmissionLatestJudgment(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.account_class_manager = security.AuthedAccount(id=2, cached_username='class_manager')

        self.submission = do.Submission(
            id=1,
            account_id=self.account.id,
            problem_id=1,
            language_id=1,
            content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            content_length=0,
            filename="filename",
            submit_time=datetime(2023, 7, 29, 12),
        )
        self.judgment = do.Judgment(
            id=1,
            submission_id=1,
            verdict=enum.VerdictType.accepted,
            total_time=1,
            max_memory=1,
            score=100,
            error_message="",
            judge_time=datetime(2023, 7, 29, 12),
        )

        self.expected_happy_flow_result = self.judgment

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            db_submission = controller.mock_module('persistence.database.submission')

            db_submission.async_func('read').call_with(
                submission_id=self.submission.id,
            ).returns(self.submission)
            db_submission.async_func('read_latest_judgment').call_with(
                submission_id=self.submission.id,
            ).returns(self.judgment)

            result = await mock.unwrap(submission.read_submission_latest_judgment)(self.submission.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_class_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account_class_manager)

            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_submission.async_func('read').call_with(
                submission_id=self.submission.id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                self.account_class_manager.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(True)
            db_submission.async_func('read_latest_judgment').call_with(
                submission_id=self.submission.id,
            ).returns(self.judgment)

            result = await mock.unwrap(submission.read_submission_latest_judgment)(self.submission.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account_class_manager)

            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_submission.async_func('read').call_with(
                submission_id=self.submission.id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                self.account_class_manager.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.read_submission_latest_judgment)(self.submission.id)


class TestRejudgeSubmission(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.submission = do.Submission(
            id=1,
            account_id=self.account.id,
            problem_id=1,
            language_id=1,
            content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            content_length=0,
            filename="filename",
            submit_time=datetime(2023, 7, 29, 12),
        )

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_judge = controller.mock_module('service.judge')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(True)
            service_judge.async_func('judge_submission').call_with(
                self.submission.id,
            ).returns(None)

            result = await mock.unwrap(submission.rejudge_submission)(self.submission.id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                submission_id=self.submission.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(submission.rejudge_submission)(self.submission.id)
