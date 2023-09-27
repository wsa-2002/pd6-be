import copy
import unittest
import uuid

from fastapi import UploadFile
import exceptions as exc

from base import enum, do
from util import mock, security

from . import testcase


class TestReadTestcase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.testcase_id = 1
        self.testcase_sample = do.Testcase(
            id=1,
            problem_id=1,
            is_sample=True,
            score=1,
            label='test',
            input_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            output_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            input_filename='test',
            output_filename='test',
            note='test',
            time_limit=1,
            memory_limit=1,
            is_disabled=True,
            is_deleted=False,
        )
        self.testcase_not_sample = do.Testcase(
            id=1,
            problem_id=1,
            is_sample=False,
            score=1,
            label='test',
            input_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            output_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            input_filename='test',
            output_filename='test',
            note='test',
            time_limit=1,
            memory_limit=1,
            is_disabled=True,
            is_deleted=False,
        )
        self.result_with_uuid = testcase.ReadTestcaseOutput(
            id=1,
            problem_id=1,
            is_sample=False,
            score=1,
            label='test',
            input_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            output_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            input_filename='test',
            output_filename='test',
            note='test',
            time_limit=1,
            memory_limit=1,
            is_disabled=True,
            is_deleted=False,
        )
        self.result_with_uuid_sample = testcase.ReadTestcaseOutput(
            id=1,
            problem_id=1,
            is_sample=True,
            score=1,
            label='test',
            input_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            output_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            input_filename='test',
            output_filename='test',
            note='test',
            time_limit=1,
            memory_limit=1,
            is_disabled=True,
            is_deleted=False,
        )
        self.result_no_uuid = testcase.ReadTestcaseOutput(
            id=1,
            problem_id=1,
            is_sample=False,
            score=1,
            label='test',
            input_file_uuid=None,
            output_file_uuid=None,
            input_filename='test',
            output_filename='test',
            note='test',
            time_limit=1,
            memory_limit=1,
            is_disabled=True,
            is_deleted=False,
        )

    async def test_happy_flow_class_normal_sample(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, testcase_id=self.testcase_id,
            ).returns(enum.RoleType.normal)
            db_testcase.async_func('read').call_with(testcase_id=self.testcase_id).returns(self.testcase_sample)

            result = await mock.unwrap(testcase.read_testcase)(self.testcase_id)

        self.assertEqual(result, self.result_with_uuid_sample)

    async def test_happy_flow_class_normal_not_sample(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, testcase_id=self.testcase_id,
            ).returns(enum.RoleType.normal)
            db_testcase.async_func('read').call_with(testcase_id=self.testcase_id).returns(self.testcase_not_sample)

            result = await mock.unwrap(testcase.read_testcase)(self.testcase_id)

        self.assertEqual(result, self.result_no_uuid)

    async def test_happy_flow_class_manager_sample(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, testcase_id=self.testcase_id,
            ).returns(enum.RoleType.manager)
            db_testcase.async_func('read').call_with(testcase_id=self.testcase_id).returns(self.testcase_sample)

            result = await mock.unwrap(testcase.read_testcase)(self.testcase_id)

        self.assertEqual(result, self.result_with_uuid_sample)

    async def test_happy_flow_class_manager_not_sample(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_rbac.async_func('get_class_role').call_with(
                context.account.id, testcase_id=self.testcase_id,
            ).returns(enum.RoleType.manager)
            db_testcase.async_func('read').call_with(testcase_id=self.testcase_id).returns(self.testcase_not_sample)

            result = await mock.unwrap(testcase.read_testcase)(self.testcase_id)

        self.assertEqual(result, self.result_with_uuid)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(testcase.read_testcase)(self.testcase_id)


class TestEditTestcase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.testcase_id = 1
        self.data = testcase.EditTestcaseInput(
            is_sample=False,
            score=1,
            time_limit=1,
            memory_limit=1,
            note='test',
            is_disabled=False,
            label='test',
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(True)
            db_testcase.async_func('edit').call_with(
                testcase_id=self.testcase_id, is_sample=self.data.is_sample, score=self.data.score,
                label=self.data.label, time_limit=self.data.time_limit, memory_limit=self.data.memory_limit,
                is_disabled=self.data.is_disabled, note=self.data.note,
            ).returns(None)

            result = await mock.unwrap(testcase.edit_testcase)(self.testcase_id, self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(testcase.edit_testcase)(self.testcase_id, self.data)


class TestUploadTestcaseInputData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.testcase_id = 1
        self.input_file = UploadFile(filename='test')
        self.no_cr_file = copy.deepcopy(self.input_file.file)
        self.s3_file = do.S3File(
            uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            bucket='bucket',
            key='key',
        )
        self.file_id = self.s3_file.uuid

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_file = controller.mock_module('util.file')
            s3_testdata = controller.mock_module('processor.http_api.testcase.s3.testdata')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(True)
            util_file.func('replace_cr').call_with(
                mock.AnyInstanceOf(type(self.input_file.file)),
            ).returns(self.no_cr_file)
            s3_testdata.async_func('upload').call_with(
                mock.AnyInstanceOf(type(self.no_cr_file)),
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(s3_file=self.s3_file).returns(self.file_id)
            db_testcase.async_func('edit').call_with(
                testcase_id=self.testcase_id, input_file_uuid=self.file_id, input_filename=self.input_file.filename,
            ).returns(None)

            result = await mock.unwrap(testcase.upload_testcase_input_data)(self.testcase_id, self.input_file)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(testcase.upload_testcase_input_data)(self.testcase_id, self.input_file)


class TestUploadTestcaseOutputData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.testcase_id = 1
        self.output_file = UploadFile(filename='test')
        self.no_cr_file = copy.deepcopy(self.output_file.file)
        self.s3_file = do.S3File(
            uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            bucket='bucket',
            key='key',
        )
        self.file_id = self.s3_file.uuid

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_file = controller.mock_module('util.file')
            s3_testdata = controller.mock_module('processor.http_api.testcase.s3.testdata')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(True)
            util_file.func('replace_cr').call_with(
                mock.AnyInstanceOf(type(self.output_file.file)),
            ).returns(self.no_cr_file)
            s3_testdata.async_func('upload').call_with(
                mock.AnyInstanceOf(type(self.no_cr_file)),
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(s3_file=self.s3_file).returns(self.file_id)
            db_testcase.async_func('edit').call_with(
                testcase_id=self.testcase_id, output_file_uuid=self.file_id, output_filename=self.output_file.filename,
            ).returns(None)

            result = await mock.unwrap(testcase.upload_testcase_output_data)(self.testcase_id, self.output_file)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(testcase.upload_testcase_output_data)(self.testcase_id, self.output_file)


class TestDeleteTestcase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.testcase_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(True)
            db_testcase.async_func('delete').call_with(testcase_id=self.testcase_id).returns(None)

            result = await mock.unwrap(testcase.delete_testcase)(self.testcase_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(testcase.delete_testcase)(self.testcase_id)


class TestDeleteTestcaseInputData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.testcase_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(True)
            db_testcase.async_func('delete_input_data').call_with(testcase_id=self.testcase_id).returns(None)

            result = await mock.unwrap(testcase.delete_testcase_input_data)(self.testcase_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(testcase.delete_testcase_input_data)(self.testcase_id)


class TestDeleteTestcaseOutputData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.testcase_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(True)
            db_testcase.async_func('delete_output_data').call_with(testcase_id=self.testcase_id).returns(None)

            result = await mock.unwrap(testcase.delete_testcase_output_data)(self.testcase_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, testcase_id=self.testcase_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(testcase.delete_testcase_output_data)(self.testcase_id)
