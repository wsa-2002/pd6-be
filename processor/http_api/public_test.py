import unittest
import uuid

import exceptions as exc

from base import enum, do
from util import mock, model

from . import public


class TestEmailVerification(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.code = uuid.UUID('{12345678-1234-5678-1234-567812345678}')

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')

            db_account.async_func('verify_email').call_with(code=self.code).returns(None)

            result = await mock.unwrap(public.email_verification)(self.code)

        self.assertIsNone(result)


class TestForgetPassword(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.data = public.ForgetPasswordInput(
            username='test',
            email=model.CaseInsensitiveEmailStr('test@pdogs.com'),
        )
        # should only be one account
        self.account = do.Account(
            id=1,
            username=self.data.username,
            nickname='nick',
            real_name='real',
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email=None)
        self.code = uuid.UUID('{12345678-1234-5678-1234-567812345678}')

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            email_forget_password = controller.mock_module('processor.http_api.public.email.forget_password')

            db_account.async_func('browse_by_email').call_with(
                self.data.email, username=self.data.username,
            ).returns([self.account])
            db_account.async_func('add_email_verification').call_with(
                email=self.data.email, account_id=self.account.id,
            ).returns(self.code)
            email_forget_password.async_func('send').call_with(to=self.data.email, code=self.code).returns(None)

            result = await mock.unwrap(public.forget_password)(self.data)

        self.assertIsNone(result)

    async def test_not_found(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')

            db_account.async_func('browse_by_email').call_with(
                self.data.email, username=self.data.username,
            ).raises(exc.persistence.NotFound)

            result = await mock.unwrap(public.forget_password)(self.data)

        self.assertIsNone(result)


class TestForgetUsername(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.data = public.ForgetUsernameInput(
            email=model.CaseInsensitiveEmailStr('test@pdogs.com'),
        )
        self.accounts = [
            do.Account(
                id=1,
                username='test1',
                nickname='nick1',
                real_name='real1',
                role=enum.RoleType.normal,
                is_deleted=False,
                alternative_email=None,
            ),
            do.Account(
                id=2,
                username='test2',
                nickname='nick2',
                real_name='real2',
                role=enum.RoleType.normal,
                is_deleted=False,
                alternative_email=self.data.email,
            ),
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            email_forget_username = controller.mock_module('processor.http_api.public.email.forget_username')

            db_account.async_func('browse_by_email').call_with(
                self.data.email, search_exhaustive=True,
            ).returns(self.accounts)
            email_forget_username.async_func('send').call_with(to=self.data.email, accounts=self.accounts).returns(None)

            result = await mock.unwrap(public.forget_username)(self.data)

        self.assertIsNone(result)

    async def test_not_found(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')

            db_account.async_func('browse_by_email').call_with(
                self.data.email, search_exhaustive=True,
            ).raises(exc.persistence.NotFound)

            result = await mock.unwrap(public.forget_username)(self.data)

        self.assertIsNone(result)
