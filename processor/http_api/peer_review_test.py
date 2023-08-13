import copy
import datetime
import unittest
import uuid

import base.popo
from base import enum, do
import exceptions as exc
from util import model
from util import mock, security

from . import peer_review


class TestReadPeerReview(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.today = datetime.datetime(2023, 4, 9)
        self.peer_review_id = 1
        self.peer_review = do.PeerReview(
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
        )
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='test',
            setter_id=1,
            description=None,
            start_time=self.today,
            end_time=self.today,
            is_deleted=False,
        )
        self.result = copy.deepcopy(self.peer_review)

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today + datetime.timedelta(days=5))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(self.peer_review_id).returns(
                self.challenge,
            )

            result = await mock.unwrap(peer_review.read_peer_review)(self.peer_review_id)

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager_preview(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today - datetime.timedelta(days=5))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.manager)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(self.peer_review_id).returns(
                self.challenge,
            )

            result = await mock.unwrap(peer_review.read_peer_review)(self.peer_review_id)

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager_normal_view(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today + datetime.timedelta(days=5))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.manager)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(self.peer_review_id).returns(
                self.challenge,
            )

            result = await mock.unwrap(peer_review.read_peer_review)(self.peer_review_id)

        self.assertEqual(result, self.result)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today + datetime.timedelta(days=5))

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.guest)

            await mock.unwrap(peer_review.read_peer_review)(self.peer_review_id)

    async def test_no_permission_hidden(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today - datetime.timedelta(days=5))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.read_peer_review)(self.peer_review_id)


class TestEditPeerReview(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.peer_review_id = 1
        self.data = peer_review.EditPeerReviewInput(
            challenge_label='test',
            title='test',
            description='test_only',
            min_score=1,
            max_score=10,
            max_review_count=10,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, peer_review_id=self.peer_review_id,
            ).returns(True)
            db_peer_review.async_func('edit').call_with(
                peer_review_id=self.peer_review_id,
                challenge_label=self.data.challenge_label,
                title=self.data.title,
                description=self.data.description,
                min_score=self.data.min_score, max_score=self.data.max_score,
                max_review_count=self.data.max_review_count,
            ).returns(None)

            result = await mock.unwrap(peer_review.edit_peer_review)(self.peer_review_id, self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, peer_review_id=self.peer_review_id,
            ).returns(False)

            await mock.unwrap(peer_review.edit_peer_review)(self.peer_review_id, self.data)


class TestDeletePeerReview(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.peer_review_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, peer_review_id=self.peer_review_id,
            ).returns(True)
            db_peer_review.async_func('delete').call_with(peer_review_id=self.peer_review_id).returns(None)

            result = await mock.unwrap(peer_review.delete_peer_review)(self.peer_review_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, peer_review_id=self.peer_review_id,
            ).returns(False)

            await mock.unwrap(peer_review.delete_peer_review)(self.peer_review_id)


class TestBrowsePeerReviewRecord(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.peer_review_id = 1
        self.filter = None
        self.filters_default = []
        self.filters_self = copy.deepcopy(self.filters_default)
        self.filters_self.append(
            base.popo.Filter(
                col_name='receiver_id',
                op=enum.FilterOperator.eq,
                value=self.login_account.id,
            ))
        self.sorter = None
        self.sorters = []
        self.limit = model.Limit(50)
        self.offset = model.Offset(0)
        self.peer_review_records = [
            do.PeerReviewRecord(
                id=1,
                peer_review_id=1,
                grader_id=1,
                receiver_id=2,
                submission_id=1,
                score=5,
                comment='soso',
                submit_time=None, ),
            do.PeerReviewRecord(
                id=2,
                peer_review_id=2,
                grader_id=1,
                receiver_id=2,
                submission_id=2,
                score=10,
                comment='great',
                submit_time=None, ),
        ]
        self.total_count = len(self.peer_review_records)
        self.browse_peer_review_record_data_normal = [
            peer_review.BrowsePeerReviewRecordOutput(
                id=record.id,
                peer_review_id=record.peer_review_id,
                grader_id=None,
                submission_id=record.submission_id,
                receiver_id=record.receiver_id,
                score=record.score,
                comment=record.comment,
                submit_time=record.submit_time,
            ) for record in self.peer_review_records
        ]
        self.browse_peer_review_record_data_manager = [
            peer_review.BrowsePeerReviewRecordOutput(
                id=record.id,
                peer_review_id=record.peer_review_id,
                grader_id=record.grader_id,
                submission_id=record.submission_id,
                receiver_id=record.receiver_id,
                score=record.score,
                comment=record.comment,
                submit_time=record.submit_time,
            ) for record in self.peer_review_records
        ]
        self.result_manager = model.BrowseOutputBase(self.browse_peer_review_record_data_manager,
                                                     self.total_count)
        self.result_normal = model.BrowseOutputBase(self.browse_peer_review_record_data_normal,
                                                    self.total_count)

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('processor.http_api.peer_review.model')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, peer_review_id=self.peer_review_id,
            ).returns(False)

            model_.func('parse_filter').call_with(self.filter, peer_review.BROWSE_PEER_REVIEW_RECORD_COLUMNS).returns(
                self.filters_default)
            model_.func('parse_sorter').call_with(self.sorter, peer_review.BROWSE_PEER_REVIEW_RECORD_COLUMNS).returns(
                self.sorters)

            db_peer_review_record.async_func('browse').call_with(
                peer_review_id=self.peer_review_id,
                limit=self.limit, offset=self.offset,
                filters=self.filters_self, sorters=self.sorters,
            ).returns(
                (self.peer_review_records, self.total_count)
            )

            model_.func('BrowseOutputBase').call_with(
                self.browse_peer_review_record_data_normal, total_count=self.total_count,
            ).returns(self.result_normal)

            result = await mock.unwrap(peer_review.browse_peer_review_record)(
                self.peer_review_id,
                self.limit, self.offset,
                self.filter, self.sorter,
            )

        self.assertEqual(result, self.result_normal)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('processor.http_api.peer_review.model')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, peer_review_id=self.peer_review_id,
            ).returns(True)

            model_.func('parse_filter').call_with(self.filter, peer_review.BROWSE_PEER_REVIEW_RECORD_COLUMNS).returns(
                self.filters_default)
            model_.func('parse_sorter').call_with(self.sorter, peer_review.BROWSE_PEER_REVIEW_RECORD_COLUMNS).returns(
                self.sorters)

            db_peer_review_record.async_func('browse').call_with(
                peer_review_id=self.peer_review_id,
                limit=self.limit, offset=self.offset,
                filters=self.filters_default, sorters=self.sorters,
            ).returns(
                (self.peer_review_records, self.total_count)
            )

            model_.func('BrowseOutputBase').call_with(
                self.browse_peer_review_record_data_manager, total_count=self.total_count,
            ).returns(self.result_manager)

            result = await mock.unwrap(peer_review.browse_peer_review_record)(
                self.peer_review_id,
                self.limit, self.offset,
                self.filter, self.sorter,
            )

        self.assertEqual(result, self.result_manager)


class TestAssignPeerReviewRecord(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.today = datetime.datetime(2023, 4, 9)
        self.peer_review_id = 1
        self.peer_review = do.PeerReview(
            id=1,
            challenge_id=1,
            challenge_label='test',
            title='test',
            target_problem_id=1,
            setter_id=1,
            description='test_only',
            min_score=1,
            max_score=10,
            max_review_count=3,
            is_deleted=False,
        )
        self.peer_review_max_limited = do.PeerReview(
            id=1,
            challenge_id=1,
            challenge_label='test',
            title='test',
            target_problem_id=1,
            setter_id=1,
            description='test_only',
            min_score=1,
            max_score=10,
            max_review_count=1,
            is_deleted=False,
        )
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='test',
            setter_id=1,
            description=None,
            start_time=self.today - datetime.timedelta(days=5),
            end_time=self.today + datetime.timedelta(days=5),
            is_deleted=False,
        )
        self.peer_review_records = [
            do.PeerReviewRecord(
                id=1,
                peer_review_id=1,
                grader_id=1,
                receiver_id=2,
                submission_id=1,
                score=5,
                comment='soso',
                submit_time=None),
            do.PeerReviewRecord(
                id=2,
                peer_review_id=2,
                grader_id=1,
                receiver_id=2,
                submission_id=2,
                score=10,
                comment='great',
                submit_time=None),
        ]
        self.peer_review_record_ids = [i + 1 for i in range(self.peer_review.max_review_count)]
        self.result = peer_review.AssignPeerReviewOutput(copy.deepcopy(self.peer_review_record_ids))

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review.challenge_id).returns(
                self.challenge,
            )
            db_peer_review_record.async_func('read_by_peer_review_id').call_with(
                peer_review_id=self.peer_review.id,
                account_id=context.account.id,
                is_receiver=False,
            ).returns(
                self.peer_review_records,
            )
            for i in range(self.peer_review.max_review_count):
                db_peer_review_record.async_func('add_auto').call_with(
                    peer_review_id=self.peer_review.id,
                    grader_id=context.account.id,
                ).returns(
                    self.peer_review_record_ids[i],
                )

            result = await mock.unwrap(peer_review.assign_peer_review_record)(self.peer_review_id)

        self.assertEqual(result, self.result)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.manager)

            await mock.unwrap(peer_review.assign_peer_review_record)(self.peer_review_id)

    async def test_no_permission_overdue(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.challenge.end_time + datetime.timedelta(days=1))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review.challenge_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.assign_peer_review_record)(self.peer_review_id)

    async def test_max_peer_reviewCount(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.MaxPeerReviewCount)
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review_max_limited,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review.challenge_id).returns(
                self.challenge,
            )
            db_peer_review_record.async_func('read_by_peer_review_id').call_with(
                peer_review_id=self.peer_review_max_limited.id,
                account_id=context.account.id,
                is_receiver=False,
            ).returns(
                self.peer_review_records,
            )

            await mock.unwrap(peer_review.assign_peer_review_record)(self.peer_review_id)


class TestReadPeerReviewRecord(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.manager = security.AuthedAccount(id=1, cached_username='manager')
        self.receiver = security.AuthedAccount(id=2, cached_username='receiver')
        self.grader = security.AuthedAccount(id=3, cached_username='grader')
        self.other_account = security.AuthedAccount(id=4, cached_username='other')
        self.today = datetime.datetime(2023, 4, 9)
        self.peer_review_record_id = 1
        self.peer_review_id = 1
        self.peer_review = do.PeerReview(
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
        )
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='test',
            setter_id=1,
            description=None,
            start_time=self.today,
            end_time=self.today,
            is_deleted=False,
        )
        self.peer_review_record = do.PeerReviewRecord(
            id=1,
            peer_review_id=1,
            grader_id=self.grader.id,
            receiver_id=self.receiver.id,
            submission_id=1,
            score=5,
            comment='soso',
            submit_time=None,
        )
        self.submission = do.Submission(
            id=1,
            account_id=1,
            problem_id=1,
            language_id=1,
            content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            content_length=1,
            filename='test',
            submit_time=self.today,
        )
        self.result_grader = peer_review.ReadPeerReviewRecordOutput(
            id=self.peer_review_record.id,
            peer_review_id=self.peer_review_record.id,
            submission_id=self.submission.id,
            grader_id=self.peer_review_record.grader_id,
            receiver_id=None,
            score=self.peer_review_record.score,
            comment=self.peer_review_record.comment,
            submit_time=self.peer_review_record.submit_time,
            filename=self.submission.filename,
            file_uuid=self.submission.content_file_uuid,
        )
        self.result_receiver = peer_review.ReadPeerReviewRecordOutput(
            id=self.peer_review_record.id,
            peer_review_id=self.peer_review_record.id,
            submission_id=self.submission.id,
            grader_id=None,
            receiver_id=self.peer_review_record.receiver_id,
            score=self.peer_review_record.score,
            comment=self.peer_review_record.comment,
            submit_time=self.peer_review_record.submit_time,
            filename=self.submission.filename,
            file_uuid=self.submission.content_file_uuid,
        )
        self.result_manager = peer_review.ReadPeerReviewRecordOutput(
            id=self.peer_review_record.id,
            peer_review_id=self.peer_review_record.id,
            submission_id=self.submission.id,
            grader_id=self.peer_review_record.grader_id,
            receiver_id=self.peer_review_record.receiver_id,
            score=self.peer_review_record.score,
            comment=self.peer_review_record.comment,
            submit_time=self.peer_review_record.submit_time,
            filename=self.submission.filename,
            file_uuid=self.submission.content_file_uuid,
        )

    async def test_happy_flow_normal_is_grader(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.grader)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.normal)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_submission.async_func('read').call_with(submission_id=self.peer_review_record.submission_id).returns(
                self.submission,
            )

            result = await mock.unwrap(peer_review.read_peer_review_record)(self.peer_review_record_id)

        self.assertEqual(result, self.result_grader)

    async def test_happy_flow_normal_is_receiver(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.receiver)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.normal)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_submission.async_func('read').call_with(submission_id=self.peer_review_record.submission_id).returns(
                self.submission,
            )

            result = await mock.unwrap(peer_review.read_peer_review_record)(self.peer_review_record_id)

        self.assertEqual(result, self.result_receiver)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.manager)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.manager)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_submission.async_func('read').call_with(submission_id=self.peer_review_record.submission_id).returns(
                self.submission,
            )

            result = await mock.unwrap(peer_review.read_peer_review_record)(self.peer_review_record_id)

        self.assertEqual(result, self.result_manager)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.grader)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.guest)

            await mock.unwrap(peer_review.read_peer_review_record)(self.peer_review_record_id)

    async def test_no_permission_other_account(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.other_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.normal)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.read_peer_review_record)(self.peer_review_record_id)

    async def test_no_permission_early(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.receiver)
            context.set_request_time(self.challenge.end_time - datetime.timedelta(days=1))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.normal)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.read_peer_review_record)(self.peer_review_record_id)


class TestSubmitPeerReviewRecord(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.today = datetime.datetime(2023, 4, 9)
        self.peer_review_record_id = 1
        self.peer_review_id = 1
        self.data = peer_review.SubmitPeerReviewInput(
            score=5,
            comment='soso',
        )
        self.data_illegal = peer_review.SubmitPeerReviewInput(
            score=100,
            comment='soso',
        )
        self.peer_review = do.PeerReview(
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
        )
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='test',
            setter_id=1,
            description=None,
            start_time=self.today - datetime.timedelta(days=5),
            end_time=self.today + datetime.timedelta(days=5),
            is_deleted=False,
        )
        self.peer_review_record = do.PeerReviewRecord(
            id=1,
            peer_review_id=1,
            grader_id=2,
            receiver_id=3,
            submission_id=1,
            score=None,
            comment=None,
            submit_time=None,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.normal)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_peer_review_record.async_func('edit_score').call_with(
                self.peer_review_record.id, score=self.data.score,
                comment=self.data.comment, submit_time=context.request_time,
            ).returns(
                self.peer_review_record,
            )

            result = await mock.unwrap(peer_review.submit_peer_review_record)(self.peer_review_record_id, self.data)

        self.assertIsNone(result)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.guest)

            await mock.unwrap(peer_review.submit_peer_review_record)(self.peer_review_record_id, self.data)

    async def test_no_permission_overdue(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.challenge.end_time + datetime.timedelta(days=1))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.normal)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.submit_peer_review_record)(self.peer_review_record_id, self.data)

    async def test_illegal_input(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.IllegalInput)
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_record_id=self.peer_review_record_id,
            ).returns(enum.RoleType.normal)
            db_peer_review_record.async_func('read').call_with(self.peer_review_record_id).returns(
                self.peer_review_record,
            )
            db_peer_review.async_func('read').call_with(peer_review_id=self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.submit_peer_review_record)(self.peer_review_record_id, self.data_illegal)


class TestBrowseAccountReceivedPeerReviewRecord(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')
        self.today = datetime.datetime(2023, 4, 9)
        self.peer_review_id = 1
        self.peer_review = do.PeerReview(
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
        )
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='test',
            setter_id=1,
            description=None,
            start_time=self.today,
            end_time=self.today,
            is_deleted=False,
        )
        self.peer_review_records = [
            do.PeerReviewRecord(
                id=1,
                peer_review_id=1,
                grader_id=1,
                receiver_id=2,
                submission_id=1,
                score=5,
                comment='soso',
                submit_time=None),
            do.PeerReviewRecord(
                id=2,
                peer_review_id=1,
                grader_id=1,
                receiver_id=2,
                submission_id=2,
                score=10,
                comment='great',
                submit_time=None),
        ]
        self.result = [record.id for record in self.peer_review_records]

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_peer_review_record.async_func('read_by_peer_review_id').call_with(
                self.peer_review_id,
                account_id=self.login_account.id,
                is_receiver=True,
            ).returns(
                self.peer_review_records,
            )

            result = await mock.unwrap(peer_review.browse_account_received_peer_review_record)(self.peer_review_id,
                                                                                               self.login_account.id)

        self.assertListEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.manager)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_peer_review_record.async_func('read_by_peer_review_id').call_with(
                self.peer_review_id,
                account_id=self.other_account.id,
                is_receiver=True,
            ).returns(
                self.peer_review_records,
            )

            result = await mock.unwrap(peer_review.browse_account_received_peer_review_record)(self.peer_review_id,
                                                                                               self.other_account.id)

        self.assertListEqual(result, self.result)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.guest)

            await mock.unwrap(peer_review.browse_account_received_peer_review_record)(self.peer_review_id,
                                                                                      self.other_account.id)

    async def test_no_permission_other_account(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.challenge.end_time)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.browse_account_received_peer_review_record)(self.peer_review_id,
                                                                                      self.other_account.id)

    async def test_no_permission_early(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.challenge.end_time - datetime.timedelta(days=1))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.browse_account_received_peer_review_record)(self.peer_review_id,
                                                                                      self.login_account.id)


class TestBrowseAccountReviewedPeerReviewRecord(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')
        self.today = datetime.datetime(2023, 4, 9)
        self.peer_review_id = 1
        self.peer_review = do.PeerReview(
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
        )
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='test',
            setter_id=1,
            description=None,
            start_time=self.today,
            end_time=self.today,
            is_deleted=False,
        )
        self.peer_review_records = [
            do.PeerReviewRecord(
                id=1,
                peer_review_id=1,
                grader_id=1,
                receiver_id=2,
                submission_id=1,
                score=5,
                comment='soso',
                submit_time=None),
            do.PeerReviewRecord(
                id=2,
                peer_review_id=1,
                grader_id=1,
                receiver_id=2,
                submission_id=2,
                score=10,
                comment='great',
                submit_time=None),
        ]
        self.result = [record.id for record in self.peer_review_records]

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_peer_review_record.async_func('read_by_peer_review_id').call_with(
                self.peer_review_id,
                account_id=self.login_account.id,
                is_receiver=False,
            ).returns(
                self.peer_review_records,
            )

            result = await mock.unwrap(peer_review.browse_account_reviewed_peer_review_record)(self.peer_review_id,
                                                                                               self.login_account.id)

        self.assertListEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review_record = controller.mock_module('persistence.database.peer_review_record')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.manager)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )
            db_peer_review_record.async_func('read_by_peer_review_id').call_with(
                self.peer_review_id,
                account_id=self.other_account.id,
                is_receiver=False,
            ).returns(
                self.peer_review_records,
            )

            result = await mock.unwrap(peer_review.browse_account_reviewed_peer_review_record)(self.peer_review_id,
                                                                                               self.other_account.id)

        self.assertListEqual(result, self.result)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.guest)

            await mock.unwrap(peer_review.browse_account_reviewed_peer_review_record)(self.peer_review_id,
                                                                                      self.login_account.id)

    async def test_no_permission_other_account(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.browse_account_reviewed_peer_review_record)(self.peer_review_id,
                                                                                      self.other_account.id)

    async def test_no_permission_early(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.challenge.start_time - datetime.timedelta(days=1))

            service_rbac = controller.mock_module('service.rbac')
            db_peer_review = controller.mock_module('persistence.database.peer_review')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, peer_review_id=self.peer_review_id,
            ).returns(enum.RoleType.normal)
            db_peer_review.async_func('read').call_with(self.peer_review_id).returns(
                self.peer_review,
            )
            db_challenge.async_func('read').call_with(challenge_id=self.peer_review_id).returns(
                self.challenge,
            )

            await mock.unwrap(peer_review.browse_account_reviewed_peer_review_record)(self.peer_review_id,
                                                                                      self.login_account.id)
