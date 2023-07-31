import unittest

from base import enum, do
from util import mock, security

from . import institute
from util import model


class TestAddInstitute(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.account = do.Account(
            id=self.login_account.id,
            username="user",
            nickname="nick",
            real_name="real",
            role=enum.RoleType.manager,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.institute = do.Institute(
            id=1,
            abbreviated_name="abbreviated",
            full_name="full",
            email_domain="email",
            is_disabled=False,
        )
        self.data = institute.AddInstituteInput(
            abbreviated_name=self.institute.abbreviated_name,
            full_name=self.institute.full_name,
            email_domain=self.institute.email_domain,
            is_disabled=self.institute.is_disabled,
        )
        self.result = model.AddOutput(id=self.institute.id)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_institute.async_func('add').call_with(
                abbreviated_name=self.data.abbreviated_name, full_name=self.data.full_name,
                email_domain=self.data.email_domain, is_disabled=self.data.is_disabled,
            ).returns(
                self.institute.id,
            )

            result = await institute.add_institute.__wrapped__(data=self.data)

        self.assertEqual(result, self.result)


class TestBrowseAllInstitute(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.all_institute = [
            do.Institute(
                id=1,
                abbreviated_name="abbreviated",
                full_name="full",
                email_domain="email",
                is_disabled=False,
            ),
            do.Institute(
                id=2,
                abbreviated_name="abbreviated",
                full_name="full",
                email_domain="email",
                is_disabled=False,
            ),
        ]
        self.result = self.all_institute

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')

            db_institute.async_func('browse').call_with().returns(
                self.all_institute,
            )

            result = await institute.browse_all_institute.__wrapped__()

        self.assertCountEqual(result, self.result)


class TestReadInstitute(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.institute = do.Institute(
            id=1,
            abbreviated_name="abbreviated",
            full_name="full",
            email_domain="email",
            is_disabled=False,
        )
        self.result = self.institute

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')

            db_institute.async_func('read').call_with(self.institute.id).returns(
                self.institute,
            )

            result = await institute.read_institute.__wrapped__(institute_id=self.institute.id)

        self.assertEqual(result, self.result)


class TestEditInstitute(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.account = do.Account(
            id=self.login_account.id,
            username="user",
            nickname="nick",
            real_name="real",
            role=enum.RoleType.manager,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.institute = do.Institute(
            id=1,
            abbreviated_name="abbreviated",
            full_name="full",
            email_domain="email",
            is_disabled=False,
        )
        self.data = institute.EditInstituteInput(
            abbreviated_name=self.institute.id,
            full_name="full_edit",
            email_domain="email_edit",
            is_disabled=False,
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_institute.async_func('edit').call_with(
                institute_id=self.institute.id, abbreviated_name=self.data.abbreviated_name,
                full_name=self.data.full_name, email_domain=self.data.email_domain,
                is_disabled=self.data.is_disabled,
            ).returns()

            result = await institute.edit_institute.__wrapped__(institute_id=self.institute.id, data=self.data)

        self.assertIsNone(result)
