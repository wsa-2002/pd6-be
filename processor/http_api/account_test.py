import copy
import unittest

from base import enum, do
from util import mock, security

from . import account


class TestReadAccountWithDefaultStudentId(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_login_account = security.AuthedAccount(id=2, cached_username='other')
        self.account = do.Account(
            id=self.login_account.id,
            username="user",
            nickname="nick",
            real_name="real",
            role=enum.RoleType.guest,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.student_card = do.StudentCard(None, None, 'id!', None, None)
        self.result = account.ReadAccountOutput(
            id=self.account.id,
            username=self.account.username,
            nickname=self.account.nickname,
            role=self.account.role,
            real_name=self.account.real_name,
            alternative_email=self.account.alternative_email,
            student_id=self.student_card.student_id,
        )
        self.non_personal_result = copy.deepcopy(self.result)
        self.non_personal_result.alternative_email = None

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account_vo = controller.mock_module('persistence.database.account_vo')

            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.manager,
            ).returns(False)
            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.normal,
            ).returns(True)
            db_account_vo.async_func('read_with_default_student_card').call_with(account_id=self.account.id).returns(
                (self.account, self.student_card),
            )

            result = await account.read_account_with_default_student_id.__wrapped__(account_id=self.account.id)

        self.assertEqual(result, self.non_personal_result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account_vo = controller.mock_module('persistence.database.account_vo')

            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.manager,
            ).returns(True)
            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.normal,
            ).returns(False)
            db_account_vo.async_func('read_with_default_student_card').call_with(account_id=self.account.id).returns(
                (self.account, self.student_card),
            )

            result = await account.read_account_with_default_student_id.__wrapped__(account_id=self.account.id)

        self.assertEqual(result, self.result)
