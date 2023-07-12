import unittest

from base import enum, do
import exceptions as exc
from util import mock, security

from . import account


class TestReadAccountWithDefaultStudentId(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        from util.context import context

        self.account_id = 1
        context.set_account(security.AuthedAccount(id=self.account_id))

        self.result = account.ReadAccountOutput(
            id=self.account_id,
            username="user",
            nickname="nick",
            role=enum.RoleType.guest,
            real_name="real",
            alternative_email="alternative",
            student_id='id!',
        )
        self.account = do.Account(
            id=self.account_id,
            username=self.result.username,
            nickname=self.result.nickname,
            real_name=self.result.real_name,
            role=self.account.role,
            is_deleted=None,
            alternative_email=self.result.alternative_email,
        )
        self.student_card = do.StudentCard(None, None, self.result.student_id, None, None)


    async def test_no_permission(self):
        with mock.Controller() as controller:

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').expect_call(self.account_id, enum.RoleType.manager).returns(False)
            service_rbac.async_func('validate_system').expect_call(self.account_id, enum.RoleType.normal).returns(False)

            with self.assertRaises(Exception) as e:
                _ = await account.read_account_with_default_student_id(account_id=2)

        self.assertTrue(isinstance(e, exc.NoPermission))

    async def test_happy_flow_manager(self):
        with mock.Controller() as controller:

            service_rbac = controller.mock_module('service.rbac')
            db_account_vo = controller.mock_module('db.account_vo')

            service_rbac.async_func('validate_system').expect_call(self.account_id, enum.RoleType.manager).returns(True)
            service_rbac.async_func('validate_system').expect_call(self.account_id, enum.RoleType.normal).returns(False)
            db_account_vo.async_func('read_with_default_student_card').expect_call(self.account_id).returns(
                self.account, self.student_card,
            )

            result = await account.read_account_with_default_student_id(account_id=self.account_id)

        self.assertEqual(result, self.result)
