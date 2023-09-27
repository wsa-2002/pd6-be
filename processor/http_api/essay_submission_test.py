import copy
import datetime
import unittest
import uuid

from fastapi import UploadFile

from base import enum, do, popo
import exceptions as exc
from util import mock, security, model

from . import essay_submission


class TestUploadEssay(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.today = datetime.datetime(2023, 4, 9)
        self.essay_id = 1
        self.essay_file = UploadFile(filename='essay')
        self.essay = do.Essay(
            id=self.essay_id,
            challenge_id=1,
            challenge_label='test',
            title='test_essay',
            setter_id=1,
            description=None,
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
        self.essay_submission_id = 1
        self.result = self.essay_submission_id

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')
            service_submission = controller.mock_module('service.submission')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_id=self.essay_id,
            ).returns(True)
            db_essay.async_func('read').call_with(essay_id=self.essay_id).returns(self.essay)
            db_challenge.async_func('read').call_with(
                self.essay.challenge_id, ref_time=context.request_time,
            ).returns(self.challenge)
            service_submission.async_func('submit_essay').call_with(
                file=mock.AnyInstanceOf(type(self.essay_file.file)), filename=self.essay_file.filename,
                account_id=context.account.id, essay_id=self.essay_id,
                submit_time=context.request_time,
            ).returns(self.essay_submission_id)

            result = await mock.unwrap(essay_submission.upload_essay)(self.essay_id, self.essay_file)

        self.assertEqual(result, self.result)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_id=self.essay_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.upload_essay)(self.essay_id, self.essay_file)

    async def test_no_permission_overdue(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.challenge.end_time)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_id=self.essay_id,
            ).returns(True)
            db_essay.async_func('read').call_with(essay_id=self.essay_id).returns(self.essay)
            db_challenge.async_func('read').call_with(
                self.essay.challenge_id, ref_time=context.request_time,
            ).returns(self.challenge)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.upload_essay)(self.essay_id, self.essay_file)


class TestBrowseEssaySubmissionByEssayId(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.today = datetime.datetime(2023, 4, 9)
        self.essay_id = 1
        self.limit = model.Limit(50)
        self.offset = model.Offset(0)
        self.filter = None
        self.filters = []
        self.filters_self = copy.deepcopy(self.filters)
        self.filters_self.append(popo.Filter(col_name='essay_id',
                                             op=enum.FilterOperator.eq,
                                             value=self.essay_id))
        self.filters_self.append(popo.Filter(col_name='account_id',
                                             op=enum.FilterOperator.eq,
                                             value=self.login_account.id))
        self.sorter = None
        self.sorters = []
        self.essay_submissions = [
            do.EssaySubmission(
                id=1,
                account_id=self.login_account.id,
                essay_id=1,
                content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
                filename='test1',
                submit_time=self.today,
            ),
            do.EssaySubmission(
                id=2,
                account_id=self.login_account.id,
                essay_id=1,
                content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345679}'),
                filename='test2',
                submit_time=self.today,
            ),
        ]
        self.total_count = len(self.essay_submissions)
        self.result = essay_submission.BrowseEssaySubmissionByEssayId(self.essay_submissions, self.total_count)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('util.model')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, essay_id=self.essay_id,
            ).returns(enum.RoleType.normal)
            model_.func('parse_filter').call_with(
                self.filter, essay_submission.BROWSE_ESSAY_SUBMISSION_COLUMNS).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter, essay_submission.BROWSE_ESSAY_SUBMISSION_COLUMNS).returns(self.sorters)
            db_essay_submission.async_func('browse').call_with(
                limit=self.limit, offset=self.offset,
                filters=self.filters_self, sorters=self.sorters,
            ).returns((self.essay_submissions, self.total_count))

            result = await mock.unwrap(essay_submission.browse_essay_submission_by_essay_id)(
                essay_id=self.essay_id,
                limit=self.limit, offset=self.offset,
                filter=self.filter, sort=self.sorter,
            )

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, essay_id=self.essay_id,
            ).returns(enum.RoleType.guest)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.browse_essay_submission_by_essay_id)(
                    essay_id=self.essay_id,
                    limit=self.limit, offset=self.offset,
                    filter=self.filter, sort=self.sorter,
                )


class TestReadEssaySubmission(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='manager')
        self.today = datetime.datetime(2023, 4, 9)
        self.essay_submission_id = 1
        self.essay_submission = do.EssaySubmission(
            id=1,
            account_id=self.login_account.id,
            essay_id=1,
            content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            filename='test1',
            submit_time=self.today,
        )
        self.result = copy.deepcopy(self.essay_submission)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, essay_submission_id=self.essay_submission_id,
            ).returns(enum.RoleType.normal)
            db_essay_submission.async_func('read').call_with(
                essay_submission_id=self.essay_submission_id,
            ).returns(self.essay_submission)

            result = await mock.unwrap(essay_submission.read_essay_submission)(self.essay_submission_id)

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, essay_submission_id=self.essay_submission_id,
            ).returns(enum.RoleType.manager)
            db_essay_submission.async_func('read').call_with(
                essay_submission_id=self.essay_submission_id,
            ).returns(self.essay_submission)

            result = await mock.unwrap(essay_submission.read_essay_submission)(self.essay_submission_id)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, essay_submission_id=self.essay_submission_id,
            ).returns(enum.RoleType.guest)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.read_essay_submission)(self.essay_submission_id)


class TestReuploadEssay(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')
        self.today = datetime.datetime(2023, 4, 9)
        self.essay_submission_id = 1
        self.essay_file = UploadFile(filename='essay')
        self.essay_submission = do.EssaySubmission(
            id=1,
            account_id=self.login_account.id,
            essay_id=1,
            content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            filename='test',
            submit_time=self.today,
        )
        self.essay = do.Essay(
            id=self.essay_submission.essay_id,
            challenge_id=1,
            challenge_label='test',
            title='test_essay',
            setter_id=1,
            description=None,
            is_deleted=False,
        )
        self.challenge = do.Challenge(
            id=self.essay.challenge_id,
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
        self.result = self.essay_submission_id

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')
            service_submission = controller.mock_module('service.submission')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_submission_id=self.essay_submission_id,
            ).returns(True)
            db_essay_submission.async_func('read').call_with(essay_submission_id=self.essay_submission_id).returns(
                self.essay_submission)
            db_essay.async_func('read').call_with(essay_id=self.essay_submission.essay_id).returns(self.essay)
            db_challenge.async_func('read').call_with(
                challenge_id=self.essay.challenge_id,
            ).returns(self.challenge)
            service_submission.async_func('resubmit_essay').call_with(
                file=mock.AnyInstanceOf(type(self.essay_file.file)), filename=self.essay_file.filename,
                essay_submission_id=self.essay_submission_id,
                submit_time=context.request_time,
            ).returns(None)

            result = await mock.unwrap(essay_submission.reupload_essay)(self.essay_submission_id, self.essay_file)

        self.assertIsNone(result)

    async def test_no_permission_unauthorized_user(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_submission_id=self.essay_submission_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.reupload_essay)(self.essay_submission_id, self.essay_file)

    async def test_no_permission_not_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)
            context.set_request_time(self.today)

            service_rbac = controller.mock_module('service.rbac')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_submission_id=self.essay_submission_id,
            ).returns(True)
            db_essay_submission.async_func('read').call_with(essay_submission_id=self.essay_submission_id).returns(
                self.essay_submission)
            db_essay.async_func('read').call_with(essay_id=self.essay_submission.essay_id).returns(self.essay)
            db_challenge.async_func('read').call_with(
                challenge_id=self.essay.challenge_id,
            ).returns(self.challenge)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.reupload_essay)(self.essay_submission_id, self.essay_file)

    async def test_no_permission_overdue(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.challenge.end_time + datetime.timedelta(days=1))

            service_rbac = controller.mock_module('service.rbac')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_submission_id=self.essay_submission_id,
            ).returns(True)
            db_essay_submission.async_func('read').call_with(essay_submission_id=self.essay_submission_id).returns(
                self.essay_submission)
            db_essay.async_func('read').call_with(essay_id=self.essay_submission.essay_id).returns(self.essay)
            db_challenge.async_func('read').call_with(
                challenge_id=self.essay.challenge_id,
            ).returns(self.challenge)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.reupload_essay)(self.essay_submission_id, self.essay_file)

    async def test_no_permission_not_self_overdue(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)
            context.set_request_time(self.challenge.end_time + datetime.timedelta(days=1))

            service_rbac = controller.mock_module('service.rbac')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, essay_submission_id=self.essay_submission_id,
            ).returns(True)
            db_essay_submission.async_func('read').call_with(essay_submission_id=self.essay_submission_id).returns(
                self.essay_submission)
            db_essay.async_func('read').call_with(essay_id=self.essay_submission.essay_id).returns(self.essay)
            db_challenge.async_func('read').call_with(
                challenge_id=self.essay.challenge_id,
            ).returns(self.challenge)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay_submission.reupload_essay)(self.essay_submission_id, self.essay_file)
