import unittest
from uuid import UUID

import exceptions as exc
from base import enum, do
from util import mock, security

from . import s3_file


class TestGetS3FileUrl(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.s3_file_uuid = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')
        self.filename = "filename"
        self.as_attachment = True

        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )
        self.url = "url"
        self.s3_file_url_output = s3_file.S3FileUrlOutput(url=self.url)

        self.expected_happy_flow_result = self.s3_file_url_output
        self.expected_not_found_result = self.s3_file_url_output

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_s3_file = controller.mock_module('persistence.database.s3_file')

            service_rbac.async_func('validate_system').call_with(
                self.account.id,
                min_role=enum.RoleType.normal,
            ).returns(True)
            db_s3_file.async_func('read').call_with(
                s3_file_uuid=self.s3_file_uuid,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                filename=self.filename, as_attachment=self.as_attachment,
            ).returns(self.url)

            result = await mock.unwrap(s3_file.get_s3_file_url)(self.s3_file_uuid, self.filename, self.as_attachment)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_not_found(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_s3_file = controller.mock_module('persistence.database.s3_file')

            service_rbac.async_func('validate_system').call_with(
                self.account.id,
                min_role=enum.RoleType.normal,
            ).returns(True)
            db_s3_file.async_func('read').call_with(
                s3_file_uuid=self.s3_file_uuid,
            ).raises(exc.persistence.NotFound)
            s3_tools.async_func('sign_url').call_with(
                bucket='temp', key=str(self.s3_file_uuid),
                filename=self.filename, as_attachment=self.as_attachment,
            ).returns(self.url)

            result = await mock.unwrap(s3_file.get_s3_file_url)(self.s3_file_uuid, self.filename, self.as_attachment)

        self.assertEqual(result, self.expected_not_found_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.account.id,
                min_role=enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(s3_file.get_s3_file_url)(self.s3_file_uuid, self.filename, self.as_attachment)
