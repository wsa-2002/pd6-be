import unittest
from uuid import UUID

from fastapi import UploadFile

import exceptions as exc
from base import enum, do
from util import mock, security

from . import assisting_data


class TestReadAssistingData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.assisting_data = do.AssistingData(
            id=1,
            problem_id=1,
            s3_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            filename="filename",
            is_deleted=False,
        )
        self.read_assisting_data_output = assisting_data.ReadAssistingDataOutput(
            id=self.assisting_data.id,
            problem_id=self.assisting_data.problem_id,
            s3_file_uuid=self.assisting_data.s3_file_uuid,
            filename=self.assisting_data.filename,
        )

        self.expected_happy_flow_result = self.read_assisting_data_output

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_assisting = controller.mock_module('persistence.database.assisting_data')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                assisting_data_id=self.assisting_data.id,
            ).returns(True)
            db_assisting.async_func('read').call_with(
                assisting_data_id=self.assisting_data.id,
            ).returns(self.assisting_data)

            result = await mock.unwrap(assisting_data.read_assisting_data)(self.assisting_data.id)

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
                assisting_data_id=self.assisting_data.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(assisting_data.read_assisting_data)(self.assisting_data.id)


class TestEditAssistingData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.assisting_data_id = 1

        self.assisting_data_file = UploadFile(filename="filename")
        self.no_cr_file = UploadFile(filename="filename")
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            util_file = controller.mock_module('util.file')
            service_rbac = controller.mock_module('service.rbac')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_assisting_data = controller.mock_module('persistence.database.assisting_data')
            s3_assisting_data = controller.mock_module('persistence.s3.assisting_data')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                assisting_data_id=self.assisting_data_id,
            ).returns(True)
            util_file.func('replace_cr').call_with(
                mock.AnyInstanceOf(type(self.assisting_data_file.file))
            ).returns(self.no_cr_file)
            s3_assisting_data.async_func('upload').call_with(
                mock.AnyInstanceOf(type(self.no_cr_file)),
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(
                s3_file=mock.AnyInstanceOf(type(self.s3_file)),
            ).returns(self.s3_file.uuid)
            db_assisting_data.async_func('edit').call_with(
                assisting_data_id=self.assisting_data_id, s3_file_uuid=self.s3_file.uuid,
                filename=self.assisting_data_file.filename,
            ).returns(None)

            result = await mock.unwrap(assisting_data.edit_assisting_data)(
                self.assisting_data_id, self.assisting_data_file,
            )

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
                assisting_data_id=self.assisting_data_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(assisting_data.edit_assisting_data)(
                    self.assisting_data_id, self.assisting_data_file,
                )


class TestDeleteAssistingData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.assisting_data_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_assisting_data = controller.mock_module('persistence.database.assisting_data')

            service_rbac.async_func('validate_class').call_with(
                self.account.id, enum.RoleType.manager,
                assisting_data_id=self.assisting_data_id,
            ).returns(True)
            db_assisting_data.async_func('delete').call_with(
                assisting_data_id=self.assisting_data_id,
            ).returns(None)

            result = await mock.unwrap(assisting_data.delete_assisting_data)(self.assisting_data_id)

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
                assisting_data_id=self.assisting_data_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(assisting_data.delete_assisting_data)(self.assisting_data_id)
