import unittest

from base import enum, do
from util import mock, security

from . import email_verification


class TestResendEmailVerification(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')
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
        self.EmailVerificationResult = do.EmailVerification(
            id=self.account.id,
            email="email",
            account_id=self.account.id,
            institute_id=self.student_card.institute_id,
            student_id=self.student_card.student_id,
            is_consumed=False,
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')
            db_email_verification = controller.mock_module('persistence.database.email_verification')
            email_send = controller.mock_module('persistence.email.verification')

            db_email_verification.async_func('read').call_with(
                email_verification_id=self.account.id
            ).returns(self.EmailVerificationResult)
            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(True)

            db_account.async_func('read').call_with(account_id=self.account.id).returns(self.account)

            code = ''
            db_email_verification.async_func('read').call_with(
                email_verification_id=self.account.id
            ).returns(self.EmailVerificationResult)
            db_email_verification.async_func('read_verification_code').call_with(
                mail_verification_id=self.account.id
            ).returns(code)
            email_send.async_func('send').call_with(
                to=self.EmailVerificationResult.email, code=code, username=self.account.username
            )

            await email_verification.resend_email_verification.__warapped__(
                email_verification_id=self.account.id
            )

    async def test_happy_flow_not_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')
            db_email_verification = controller.mock_module('persistence.database.email_verification')
            email_send = controller.mock_module('persistence.email.verification')

            db_email_verification.async_func('read').call_with(
                email_verification_id=self.account.id
            ).returns(self.EmailVerificationResult)
            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(False)

            db_account.async_func('read').call_with(account_id=self.account.id).returns(self.account)

            code = ''
            db_email_verification.async_func('read').call_with(
                email_verification_id=self.account.id
            ).returns(self.EmailVerificationResult)
            db_email_verification.async_func('read_verification_code').call_with(
                mail_verification_id=self.account.id
            ).returns(code)
            email_send.async_func('send').call_with(
                to=self.EmailVerificationResult.email, code=code, username=self.account.username
            )

            await email_verification.resend_email_verification.__warapped__(
                email_verification_id=self.account.id
            )


class TestDeletePendingEmailVerification(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')
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
        self.EmailVerificationResult = do.EmailVerification(
            id=self.account.id,
            email="email",
            account_id=self.account.id,
            institute_id=self.student_card.institute_id,
            student_id=self.student_card.student_id,
            is_consumed=False,
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')
            db_email_verification_read = controller.mock_module('persistence.database.email_verification')

            db_email_verification_read.async_func('read').call_with(
                email_verification_id=self.account.id
            ).returns(self.EmailVerificationResult)
            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(True)
            db_email_verification_read.async_func('delete').call_with(
                email_verification_id=self.account.id
            )

            await email_verification.delete_pending_email_verification.__warapped__(
                email_verification_id=self.account.id
            )

    async def test_happy_flow_not_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')
            db_email_verification_read = controller.mock_module('persistence.database.email_verification')

            db_email_verification_read.async_func('read').call_with(
                email_verification_id=self.account.id
            ).returns(self.EmailVerificationResult)
            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(False)
            db_email_verification_read.async_func('delete').call_with(
                email_verification_id=self.account.id
            )

            await email_verification.delete_pending_email_verification.__warapped__(
                email_verification_id=self.account.id
            )
