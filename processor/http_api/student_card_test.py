import pydantic
import unittest

from base import enum, do
import exceptions as exc
from util import mock, security, model

from . import student_card


class TestAddStudentCardToAccount(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_login_account = security.AuthedAccount(id=2, cached_username='other')

        self.input_data = student_card.AddStudentCardInput(
            institute_id=1,
            institute_email_prefix='b1234',
            student_id='b1234',
        )
        self.invalid_input_data = student_card.AddStudentCardInput(
            institute_id=1,
            institute_email_prefix='b1234',
            student_id='b5678',
        )
        self.institute = do.Institute(
            id=1,
            abbreviated_name='abbreviate_name',
            full_name='full_name',
            email_domain='ntu.im',
            is_disabled=False,
        )
        self.institute_email = 'b1234@ntu.im'
        self.account = do.Account(
            id=1,
            username='username1',
            nickname='nickname1',
            real_name='real_name1',
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email='alternative1@gmail.com',
        )
        self.code = '12345'

        self.add_result = model.AddOutput(id=1)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')
            db_account = controller.mock_module('persistence.database.account')
            email_ = controller.mock_module('persistence.email.verification')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)

            db_institute.async_func('read').call_with(
                self.input_data.institute_id, include_disabled=False,
            ).returns(self.institute)

            db_student_card.async_func('is_duplicate').call_with(
                self.institute.id, self.input_data.student_id,
            ).returns(False)

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                model.CaseInsensitiveEmailStr, self.institute_email,
            ).returns(self.institute_email)

            db_account.async_func('add_email_verification').call_with(
                email=self.institute_email, account_id=self.other_login_account.id,
                institute_id=self.input_data.institute_id, student_id=self.input_data.student_id,
            ).returns(self.code)

            db_account.async_func('read').call_with(
                self.other_login_account.id,
            ).returns(self.account)
            email_.async_func('send').call_with(
                to=self.institute_email, code=self.code, username=self.account.username,
            ).returns(None)

            result = await mock.unwrap(student_card.add_student_card_to_account)(
                account_id=self.other_login_account.id,
                data=self.input_data,
            )

        self.assertIsNone(result)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')
            db_account = controller.mock_module('persistence.database.account')
            email_ = controller.mock_module('persistence.email.verification')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_institute.async_func('read').call_with(
                self.input_data.institute_id, include_disabled=False,
            ).returns(self.institute)

            db_student_card.async_func('is_duplicate').call_with(
                self.institute.id, self.input_data.student_id,
            ).returns(False)

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                model.CaseInsensitiveEmailStr, self.institute_email,
            ).returns(self.institute_email)

            db_account.async_func('add_email_verification').call_with(
                email=self.institute_email, account_id=self.login_account.id,
                institute_id=self.input_data.institute_id, student_id=self.input_data.student_id,
            ).returns(self.code)

            db_account.async_func('read').call_with(
                self.login_account.id,
            ).returns(self.account)
            email_.async_func('send').call_with(
                to=self.institute_email, code=self.code, username=self.account.username,
            ).returns(None)

            result = await mock.unwrap(student_card.add_student_card_to_account)(
                account_id=self.login_account.id,
                data=self.input_data,
            )

        self.assertIsNone(result)

    async def test_invalid_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_institute.async_func('read').call_with(
                self.input_data.institute_id, include_disabled=False,
            ).returns(self.institute)

            db_student_card.async_func('is_duplicate').call_with(
                self.institute.id, self.input_data.student_id,
            ).returns(False)

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                model.CaseInsensitiveEmailStr, self.institute_email,
            ).raises(pydantic.EmailError)

            with self.assertRaises(exc.account.InvalidEmail):
                await mock.unwrap(student_card.add_student_card_to_account)(
                    account_id=self.login_account.id,
                    data=self.input_data,
                )

    async def test_student_card_exists(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_institute.async_func('read').call_with(
                self.input_data.institute_id, include_disabled=False,
            ).returns(self.institute)

            db_student_card.async_func('is_duplicate').call_with(
                self.institute.id, self.input_data.student_id,
            ).returns(True)

            with self.assertRaises(exc.account.StudentCardExists):
                await mock.unwrap(student_card.add_student_card_to_account)(
                    account_id=self.login_account.id,
                    data=self.input_data,
                )

    async def test_not_match_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_institute.async_func('read').call_with(
                self.invalid_input_data.institute_id, include_disabled=False,
            ).returns(self.institute)

            with self.assertRaises(exc.account.StudentIdNotMatchEmail):
                await mock.unwrap(student_card.add_student_card_to_account)(
                    account_id=self.login_account.id,
                    data=self.invalid_input_data,
                )

    async def test_invalid_institute(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_institute = controller.mock_module('persistence.database.institute')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_institute.async_func('read').call_with(
                self.input_data.institute_id, include_disabled=False,
            ).raises(exc.persistence.NotFound)

            with self.assertRaises(exc.account.InvalidInstitute):
                await mock.unwrap(student_card.add_student_card_to_account)(
                    account_id=self.login_account.id,
                    data=self.input_data,
                )

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(student_card.add_student_card_to_account)(
                    account_id=self.other_login_account.id,
                    data=self.input_data,
                )


class TestBrowseAllAccountStudentCard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_login_account = security.AuthedAccount(id=2, cached_username='other')

        self.expected_output_data = [
            do.StudentCard(
                id=1,
                institute_id=1,
                student_id='id1',
                email='email1@gmail.com',
                is_default=True,
            ),
            do.StudentCard(
                id=2,
                institute_id=2,
                student_id='id2',
                email='email2@gmail.com',
                is_default=True,
            ),
        ]

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_student_card = controller.mock_module('persistence.database.student_card')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)

            db_student_card.async_func('browse').call_with(
                account_id=self.other_login_account.id,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(student_card.browse_all_account_student_card)(
                account_id=self.other_login_account.id,
            )

        self.assertEqual(result, self.expected_output_data)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_student_card = controller.mock_module('persistence.database.student_card')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_student_card.async_func('browse').call_with(
                account_id=self.login_account.id,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(student_card.browse_all_account_student_card)(
                account_id=self.login_account.id,
            )

        self.assertEqual(result, self.expected_output_data)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(student_card.browse_all_account_student_card)(
                    account_id=self.other_login_account.id,
                )


class TestReadStudentCard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_login_account = security.AuthedAccount(id=2, cached_username='other')

        self.student_card_id = 1
        self.owner_id = 2

        self.expected_output_data = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='id1',
            email='email1@gmail.com',
            is_default=True,
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_student_card = controller.mock_module('persistence.database.student_card')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_student_card.async_func('read_owner_id').call_with(
                student_card_id=self.student_card_id,
            ).returns(self.owner_id)

            db_student_card.async_func('read').call_with(
                student_card_id=self.student_card_id,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(student_card.read_student_card)(
                student_card_id=self.student_card_id,
            )

        self.assertEqual(result, self.expected_output_data)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_student_card = controller.mock_module('persistence.database.student_card')

            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.manager,
            ).returns(False)
            db_student_card.async_func('read_owner_id').call_with(
                student_card_id=self.student_card_id,
            ).returns(self.owner_id)

            db_student_card.async_func('read').call_with(
                student_card_id=self.student_card_id,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(student_card.read_student_card)(
                student_card_id=self.student_card_id,
            )

        self.assertEqual(result, self.expected_output_data)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_student_card = controller.mock_module('persistence.database.student_card')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)
            db_student_card.async_func('read_owner_id').call_with(
                student_card_id=self.student_card_id,
            ).returns(self.owner_id)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(student_card.read_student_card)(
                    student_card_id=self.student_card_id,
                )
