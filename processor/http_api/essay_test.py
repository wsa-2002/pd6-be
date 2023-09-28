from datetime import datetime
import typing
import unittest
from uuid import UUID

from fastapi import BackgroundTasks

import const
import exceptions as exc
from base import enum, do
from util import mock, security

from . import essay


class TestReadEssay(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.request_time = datetime(2023, 7, 28, 12)
        self.request_time_before_start = datetime(2023, 7, 27, 12)

        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title="title",
            setter_id=self.account.id,
            description="desc",
            start_time=datetime(2023, 7, 28),
            end_time=datetime(2023, 7, 29),
            is_deleted=False,
        )
        self.essay = do.Essay(
            id=1,
            challenge_id=self.challenge.id,
            challenge_label="challenge",
            title="title",
            setter_id=self.account.id,
            description="desc",
            is_deleted=False,
        )

        self.expected_happy_flow_result = self.essay
        self.expected_normal_after_start_result = self.essay

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                self.account.id, essay_id=self.essay.id,
            ).returns(enum.RoleType.manager)
            db_essay.async_func('read').call_with(
                essay_id=self.essay.id,
            ).returns(self.essay)
            db_challenge.async_func('read').call_with(
                self.essay.challenge_id,
            ).returns(self.challenge)

            result = await mock.unwrap(essay.read_essay)(self.essay.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_normal_after_start(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                self.account.id, essay_id=self.essay.id,
            ).returns(enum.RoleType.normal)
            db_essay.async_func('read').call_with(
                essay_id=self.essay.id,
            ).returns(self.essay)
            db_challenge.async_func('read').call_with(
                self.essay.challenge_id,
            ).returns(self.challenge)

            result = await mock.unwrap(essay.read_essay)(self.essay.id)

        self.assertEqual(result, self.expected_normal_after_start_result)

    async def test_normal_before_start(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time_before_start)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                self.account.id, essay_id=self.essay.id,
            ).returns(enum.RoleType.normal)
            db_essay.async_func('read').call_with(
                essay_id=self.essay.id,
            ).returns(self.essay)
            db_challenge.async_func('read').call_with(
                self.essay.challenge_id,
            ).returns(self.challenge)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay.read_essay)(self.essay.id)

    async def test_no_permission_guest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('get_class_role').call_with(
                self.account.id, essay_id=self.essay.id,
            ).returns(enum.RoleType.guest)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay.read_essay)(self.essay.id)


class TestEditEssay(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.essay_id = 1
        self.data = essay.EditEssayInput(
            title="title",
            challenge_label="challenge",
            description="desc",
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                essay_id=self.essay_id,
            ).returns(True)
            db_essay.async_func('edit').call_with(
                essay_id=self.essay_id, setter_id=self.account.id,
                title=self.data.title, challenge_label=self.data.challenge_label,
                description=self.data.description,
            ).returns(None)

            result = await mock.unwrap(essay.edit_essay)(self.essay_id, self.data)

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
                essay_id=self.essay_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay.edit_essay)(self.essay_id, self.data)


class TestDeleteEssay(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.essay_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_essay = controller.mock_module('persistence.database.essay')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                essay_id=self.essay_id,
            ).returns(True)
            db_essay.async_func('delete').call_with(
                essay_id=self.essay_id,
            ).returns(None)

            result = await mock.unwrap(essay.delete_essay)(self.essay_id)

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
                essay_id=self.essay_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay.delete_essay)(self.essay_id)


class TestDownloadAllEssaySubmission(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.essay = do.Essay(
            id=1,
            challenge_id=1,
            challenge_label="challenge",
            title="title",
            setter_id=self.account.id,
            description="desc",
            is_deleted=False,
        )
        self.background_tasks = BackgroundTasks()
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'essay_submission.zip'
        self.file_url = 'file_url'
        self.account = do.Account(
            id=1,
            username='username',
            nickname='',
            real_name='',
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email=None,
        )
        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='1',
            email='email',
            is_default=True,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, essay_id=self.essay.id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(essay.download_all_essay_submission)(essay_id=self.essay.id,
                                                                            as_attachment=True,
                                                                            background_tasks=self.background_tasks)
            service_downloader.async_func('all_essay_submissions').call_with(
                essay_id=self.essay.id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                filename=self.filename, as_attachment=True,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(
                (self.account, self.student_card),
            )

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email, file_url=self.file_url,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, essay_id=self.essay.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(essay.download_all_essay_submission)(essay_id=self.essay.id,
                                                                       as_attachment=True,
                                                                       background_tasks=self.background_tasks)
