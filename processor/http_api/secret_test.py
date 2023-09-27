import copy
import unittest
import uuid

import pydantic
from fastapi import UploadFile

from base import enum, do
import exceptions as exc
from config import config
from util import mock, security, model

from . import secret


class TestAddAccount(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.data = secret.AddAccountInput(
            username='test',
            password='123',
            nickname='nick',
            real_name='real',
            # Student card
            institute_id=1,
            student_id='test',
            institute_email_prefix='test',
        )
        self.data_with_alt = secret.AddAccountInput(
            username='test',
            password='123',
            nickname='nick',
            real_name='real',
            alternative_email=model.CaseInsensitiveEmailStr('test@pdogs.com'),
            # Student card
            institute_id=1,
            student_id='test',
            institute_email_prefix='test',
        )
        self.data_no_alt = secret.AddAccountInput(
            username='test',
            password='123',
            nickname='nick',
            real_name='real',
            alternative_email=None,
            # Student card
            institute_id=1,
            student_id='test',
            institute_email_prefix='test',
        )
        self.data_illegal_char = secret.AddAccountInput(
            username='#totally_legal',
            password='123',
            nickname='nick',
            real_name='real',
            # Student card
            institute_id=1,
            student_id='test',
            institute_email_prefix='test',
        )
        self.data_mismatch = secret.AddAccountInput(
            username='test',
            password='123',
            nickname='nick',
            real_name='real',
            # Student card
            institute_id=1,
            student_id='test',
            institute_email_prefix='tset',
        )
        self.institute = do.Institute(
            id=1,
            abbreviated_name='test',
            full_name='test_institute',
            email_domain='email.com',
            is_disabled=False,
        )
        self.account_id = 1
        self.institute_email = f"{self.data.institute_email_prefix}@{self.institute.email_domain}"
        self.institute_email_case_insensitive = copy.deepcopy(self.institute_email)
        self.hashed_password = '123'
        self.code_main = uuid.UUID('{12345678-1234-5678-1234-567812345678}')
        self.code_alt = uuid.UUID('{87654321-8765-4321-8765-432187654321}')
        self.account = do.Account(
            id=self.account_id,
            username=self.data.username,
            nickname=self.data.nickname,
            real_name=self.data.real_name,
            role=enum.RoleType.guest,
            is_deleted=False,
            alternative_email=None,
        )

    async def test_happy_flow_default_alt_email(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')
            email_verification = controller.mock_module('processor.http_api.secret.email.verification')

            db_institute.async_func('read').call_with(
                self.data.institute_id, include_disabled=False,
            ).returns(self.institute)
            db_student_card.async_func('is_duplicate').call_with(self.institute.id, self.data.student_id).returns(False)
            security_.func('hash_password').call_with(self.data.password).returns(self.hashed_password)
            db_account.async_func('add').call_with(
                username=self.data.username, pass_hash=self.hashed_password,
                nickname=self.data.nickname, real_name=self.data.real_name, role=enum.RoleType.guest,
            ).returns(self.account_id)
            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                model.CaseInsensitiveEmailStr, self.institute_email,
            ).returns(self.institute_email_case_insensitive)
            db_account.async_func('add_email_verification').call_with(
                email=self.institute_email, account_id=self.account_id,
                institute_id=self.data.institute_id, student_id=self.data.student_id,
            ).returns(self.code_main)
            db_account.async_func('read').call_with(self.account_id).returns(self.account)
            email_verification.async_func('send').call_with(
                to=self.institute_email, code=self.code_main, username=self.account.username,
            ).returns(None)

            result = await mock.unwrap(secret.add_account)(self.data)

        self.assertIsNone(result)

    async def test_happy_flow_with_alt_email(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')
            email_verification = controller.mock_module('processor.http_api.secret.email.verification')

            db_institute.async_func('read').call_with(
                self.data_with_alt.institute_id, include_disabled=False,
            ).returns(self.institute)
            db_student_card.async_func('is_duplicate').call_with(
                self.institute.id, self.data_with_alt.student_id,
            ).returns(False)
            security_.func('hash_password').call_with(self.data_with_alt.password).returns(self.hashed_password)
            db_account.async_func('add').call_with(
                username=self.data_with_alt.username, pass_hash=self.hashed_password,
                nickname=self.data_with_alt.nickname, real_name=self.data_with_alt.real_name, role=enum.RoleType.guest,
            ).returns(self.account_id)
            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                model.CaseInsensitiveEmailStr, self.institute_email,
            ).returns(self.institute_email_case_insensitive)
            db_account.async_func('add_email_verification').call_with(
                email=self.institute_email, account_id=self.account_id,
                institute_id=self.data_with_alt.institute_id, student_id=self.data_with_alt.student_id,
            ).returns(self.code_main)
            db_account.async_func('read').call_with(self.account_id).returns(self.account)
            email_verification.async_func('send').call_with(
                to=self.institute_email, code=self.code_main, username=self.account.username,
            ).returns(None)

            db_account.async_func('add_email_verification').call_with(
                email=self.data_with_alt.alternative_email, account_id=self.account_id,
            ).returns(self.code_alt)
            db_account.async_func('read').call_with(self.account_id).returns(self.account)
            email_verification.async_func('send').call_with(
                to=self.data_with_alt.alternative_email, code=self.code_alt, username=self.account.username,
            ).returns(None)

            result = await mock.unwrap(secret.add_account)(self.data_with_alt)

        self.assertIsNone(result)

    async def test_happy_flow_no_alt_email(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')
            email_verification = controller.mock_module('processor.http_api.secret.email.verification')

            db_institute.async_func('read').call_with(
                self.data_no_alt.institute_id, include_disabled=False,
            ).returns(self.institute)
            db_student_card.async_func('is_duplicate').call_with(
                self.institute.id, self.data_no_alt.student_id,
            ).returns(False)
            security_.func('hash_password').call_with(self.data_no_alt.password).returns(self.hashed_password)
            db_account.async_func('add').call_with(
                username=self.data_no_alt.username, pass_hash=self.hashed_password,
                nickname=self.data_no_alt.nickname, real_name=self.data_no_alt.real_name, role=enum.RoleType.guest,
            ).returns(self.account_id)
            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                model.CaseInsensitiveEmailStr, self.institute_email,
            ).returns(self.institute_email_case_insensitive)
            db_account.async_func('add_email_verification').call_with(
                email=self.institute_email, account_id=self.account_id,
                institute_id=self.data_no_alt.institute_id, student_id=self.data_no_alt.student_id,
            ).returns(self.code_main)
            db_account.async_func('read').call_with(self.account_id).returns(self.account)
            email_verification.async_func('send').call_with(
                to=self.institute_email, code=self.code_main, username=self.account.username,
            ).returns(None)

            db_account.async_func('delete_alternative_email_by_id').call_with(account_id=self.account_id).returns(None)

            result = await mock.unwrap(secret.add_account)(self.data_no_alt)

        self.assertIsNone(result)

    async def test_illegal_character(self):
        with self.assertRaises(exc.account.IllegalCharacter):
            await mock.unwrap(secret.add_account)(self.data_illegal_char)

    async def test_invalid_institute(self):
        with mock.Controller() as controller:
            db_institute = controller.mock_module('persistence.database.institute')

            db_institute.async_func('read').call_with(
                self.data.institute_id, include_disabled=False,
            ).raises(exc.persistence.NotFound)

            with self.assertRaises(exc.account.InvalidInstitute):
                await mock.unwrap(secret.add_account)(self.data)

    async def test_student_id_not_match_email(self):
        with mock.Controller() as controller:
            db_institute = controller.mock_module('persistence.database.institute')

            db_institute.async_func('read').call_with(
                self.data.institute_id, include_disabled=False,
            ).returns(self.institute)

            with self.assertRaises(exc.account.StudentIdNotMatchEmail):
                await mock.unwrap(secret.add_account)(self.data_mismatch)

    async def test_student_card_exists(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')

            db_institute.async_func('read').call_with(
                self.data.institute_id, include_disabled=False,
            ).returns(self.institute)
            db_student_card.async_func('is_duplicate').call_with(self.institute.id, self.data.student_id).returns(True)

            with self.assertRaises(exc.account.StudentCardExists):
                await mock.unwrap(secret.add_account)(self.data)

    async def test_username_exists(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_institute.async_func('read').call_with(
                self.data.institute_id, include_disabled=False,
            ).returns(self.institute)
            db_student_card.async_func('is_duplicate').call_with(self.institute.id, self.data.student_id).returns(False)
            security_.func('hash_password').call_with(self.data.password).returns(self.hashed_password)
            db_account.async_func('add').call_with(
                username=self.data.username, pass_hash=self.hashed_password,
                nickname=self.data.nickname, real_name=self.data.real_name, role=enum.RoleType.guest,
            ).raises(exc.persistence.UniqueViolationError)

            with self.assertRaises(exc.account.UsernameExists):
                await mock.unwrap(secret.add_account)(self.data)

    async def test_invalid_email(self):
        with (
            mock.Controller() as controller,
        ):
            db_institute = controller.mock_module('persistence.database.institute')
            db_student_card = controller.mock_module('persistence.database.student_card')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_institute.async_func('read').call_with(
                self.data.institute_id, include_disabled=False,
            ).returns(self.institute)
            db_student_card.async_func('is_duplicate').call_with(self.institute.id, self.data.student_id).returns(False)
            security_.func('hash_password').call_with(self.data.password).returns(self.hashed_password)
            db_account.async_func('add').call_with(
                username=self.data.username, pass_hash=self.hashed_password,
                nickname=self.data.nickname, real_name=self.data.real_name, role=enum.RoleType.guest,
            ).returns(self.account_id)
            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                model.CaseInsensitiveEmailStr, self.institute_email,
            ).raises(pydantic.EmailError)

            with self.assertRaises(exc.account.InvalidEmail):
                await mock.unwrap(secret.add_account)(self.data)

    async def test_invalid_username(self):
        with self.assertRaises(pydantic.ValidationError):
            self.data_empty_username = secret.AddAccountInput(
                username='',
                password='123',
                nickname='nick',
                real_name='real',
                # Student card
                institute_id=1,
                student_id='test',
                institute_email_prefix='test',
            )

    async def test_invalid_password(self):
        with self.assertRaises(pydantic.ValidationError):
            self.data_empty_password = secret.AddAccountInput(
                username='test',
                password='',
                nickname='nick',
                real_name='real',
                # Student card
                institute_id=1,
                student_id='test',
                institute_email_prefix='test',
            )


class TestLogin(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.data = secret.LoginInput(
            username='test',
            password='123',
        )
        self.account_id = 1
        self.pass_hash = 'hash'
        self.login_token = 'jwt_token'
        self.result = secret.LoginOutput(
            token=self.login_token,
            account_id=self.account_id,
        )

    async def test_happy_flow_not_4s_hash(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_account.async_func('read_login_by_username').call_with(username=self.data.username).returns(
                (self.account_id, self.pass_hash, False),
            )
            security_.func('verify_password').call_with(to_test=self.data.password, hashed=self.pass_hash).returns(True)
            security_.func('encode_jwt').call_with(
                account_id=self.account_id, expire=config.login_expire, cached_username=self.data.username,
            ).returns(self.login_token)

            result = await mock.unwrap(secret.login)(self.data)

        self.assertEqual(result, self.result)

    async def test_happy_flow_4s_hash(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_account.async_func('read_login_by_username').call_with(username=self.data.username).returns(
                (self.account_id, self.pass_hash, True),
            )
            security_.func('verify_password_4s').call_with(
                to_test=self.data.password, hashed=self.pass_hash,
            ).returns(True)
            security_.func('hash_password').call_with(self.data.password).returns(self.pass_hash)
            db_account.async_func('edit_pass_hash').call_with(
                account_id=self.account_id, pass_hash=self.pass_hash,
            ).returns(None)
            security_.func('encode_jwt').call_with(
                account_id=self.account_id, expire=config.login_expire, cached_username=self.data.username,
            ).returns(self.login_token)

            result = await mock.unwrap(secret.login)(self.data)

        self.assertEqual(result, self.result)

    async def test_login_failed_account_not_found(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')

            db_account.async_func('read_login_by_username').call_with(username=self.data.username).raises(
                exc.persistence.NotFound,
            )

            with self.assertRaises(exc.account.LoginFailed):
                await mock.unwrap(secret.login)(self.data)

    async def test_login_failed_not_4s_hash_verification_failed(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_account.async_func('read_login_by_username').call_with(username=self.data.username).returns(
                (self.account_id, self.pass_hash, False),
            )
            security_.func('verify_password').call_with(to_test=self.data.password,
                                                        hashed=self.pass_hash).returns(False)

            with self.assertRaises(exc.account.LoginFailed):
                await mock.unwrap(secret.login)(self.data)

    async def test_login_failed_4s_hash_verification_failed(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_account.async_func('read_login_by_username').call_with(username=self.data.username).returns(
                (self.account_id, self.pass_hash, True),
            )
            security_.func('verify_password_4s').call_with(to_test=self.data.password,
                                                           hashed=self.pass_hash).returns(False)

            with self.assertRaises(exc.account.LoginFailed):
                await mock.unwrap(secret.login)(self.data)


class TestAddNormalAccount(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.data = secret.AddNormalAccountInput(
            real_name='real',
            username='test',
            password='123',
            nickname='nick',
            alternative_email=model.CaseInsensitiveEmailStr('test@email.com'),
        )
        self.data_no_alt = secret.AddNormalAccountInput(
            real_name='real',
            username='test',
            password='123',
            nickname='nick',
            alternative_email=None,
        )
        self.data_illegal_char = secret.AddNormalAccountInput(
            real_name='real',
            username='#totally_legal',
            password='123',
            nickname='nick',
            alternative_email=model.CaseInsensitiveEmailStr('test@email.com'),
        )
        self.account_id = 1
        self.pass_hash = 'hash'
        self.login_token = 'jwt_token'
        self.result = model.AddOutput(
            id=self.account_id,
        )

    async def test_happy_flow_with_alt_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            security_.func('hash_password').call_with(self.data.password).returns(self.pass_hash)
            db_account.async_func('add_normal').call_with(
                username=self.data.username,
                pass_hash=self.pass_hash,
                real_name=self.data.real_name, nickname=self.data.nickname,
                alternative_email=self.data.alternative_email,
            ).returns(
                self.account_id,
            )

            result = await mock.unwrap(secret.add_normal_account)(self.data)

        self.assertEqual(result, self.result)

    async def test_happy_flow_no_alt_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            security_.func('hash_password').call_with(self.data_no_alt.password).returns(self.pass_hash)
            db_account.async_func('add_normal').call_with(
                username=self.data_no_alt.username,
                pass_hash=self.pass_hash,
                real_name=self.data_no_alt.real_name, nickname=self.data_no_alt.nickname,
                alternative_email=None,
            ).returns(
                self.account_id,
            )

            result = await mock.unwrap(secret.add_normal_account)(self.data_no_alt)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(secret.add_normal_account)(self.data)

    async def test_illegal_character(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)

            with self.assertRaises(exc.account.IllegalCharacter):
                await mock.unwrap(secret.add_normal_account)(self.data_illegal_char)

    async def test_username_exists(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            security_.func('hash_password').call_with(self.data.password).returns(self.pass_hash)
            db_account.async_func('add_normal').call_with(
                username=self.data.username,
                pass_hash=self.pass_hash,
                real_name=self.data.real_name, nickname=self.data.nickname,
                alternative_email=self.data.alternative_email,
            ).raises(exc.persistence.UniqueViolationError)

            with self.assertRaises(exc.account.UsernameExists):
                await mock.unwrap(secret.add_normal_account)(self.data)

    async def test_invalid_username(self):
        with self.assertRaises(pydantic.ValidationError):
            self.data_empty_username = secret.AddNormalAccountInput(
                real_name='real',
                username='',
                password='123',
                nickname='nick',
                alternative_email=model.CaseInsensitiveEmailStr('test@email.com'),
            )

    async def test_invalid_password(self):
        with self.assertRaises(pydantic.ValidationError):
            self.data_empty_password = secret.AddNormalAccountInput(
                real_name='real',
                username='test',
                password='',
                nickname='nick',
                alternative_email=model.CaseInsensitiveEmailStr('test@email.com'),
            )


class TestImportAccount(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.account_file = UploadFile(filename='account')

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_csv = controller.mock_module('service.csv')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            service_csv.async_func('import_account').call_with(
                account_file=mock.AnyInstanceOf(type(self.account_file.file)),
            ).returns(None)

            result = await mock.unwrap(secret.import_account)(self.account_file)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(secret.import_account)(self.account_file)


class TestEditPassword(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='manager')
        self.account_id = 1
        self.data = secret.EditPasswordInput(
            old_password='old',
            new_password='new',
        )
        self.pass_hash_old = 'old_hash'
        self.pass_hash_new = 'new_hash'

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_account.async_func('read_pass_hash').call_with(
                account_id=self.account_id, include_4s_hash=False,
            ).returns(self.pass_hash_old)
            security_.func('verify_password').call_with(
                to_test=self.data.old_password, hashed=self.pass_hash_old,
            ).returns(True)
            security_.func('hash_password').call_with(self.data.new_password).returns(self.pass_hash_new)
            db_account.async_func('edit_pass_hash').call_with(
                account_id=self.account_id, pass_hash=self.pass_hash_new,
            ).returns(None)

            result = await mock.unwrap(secret.edit_password)(self.account_id, self.data)

        self.assertIsNone(result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            security_.func('hash_password').call_with(self.data.new_password).returns(self.pass_hash_new)
            db_account.async_func('edit_pass_hash').call_with(
                account_id=self.account_id, pass_hash=self.pass_hash_new,
            ).returns(None)

            result = await mock.unwrap(secret.edit_password)(self.account_id, self.data)

        self.assertIsNone(result)

    async def test_password_verification_failed(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_account = controller.mock_module('persistence.database.account')
            security_ = controller.mock_module('processor.http_api.secret.security')

            db_account.async_func('read_pass_hash').call_with(
                account_id=self.account_id, include_4s_hash=False,
            ).returns(self.pass_hash_old)
            security_.func('verify_password').call_with(
                to_test=self.data.old_password, hashed=self.pass_hash_old,
            ).returns(False)

            with self.assertRaises(exc.account.PasswordVerificationFailed):
                await mock.unwrap(secret.edit_password)(self.account_id, self.data)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(secret.edit_password)(self.account_id, self.data)

    async def test_invalid_password(self):
        with self.assertRaises(pydantic.ValidationError):
            self.data_empty_password = secret.EditPasswordInput(
                old_password='old',
                new_password='',
            )


class TestResetPassword(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.data = secret.ResetPasswordInput(
            code=str(uuid.UUID('{12345678-1234-5678-1234-567812345678}')),
            password='123',
        )

        self.pass_hash = 'hash'

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            security_ = controller.mock_module('processor.http_api.secret.security')
            db_account = controller.mock_module('persistence.database.account')

            security_.func('hash_password').call_with(self.data.password).returns(self.pass_hash)
            db_account.async_func('reset_password').call_with(
                code=self.data.code, password_hash=self.pass_hash,
            ).returns(None)

            result = await mock.unwrap(secret.reset_password)(self.data)

        self.assertIsNone(result)

    async def test_invalid_password(self):
        with self.assertRaises(pydantic.ValidationError):
            self.data_empty_password = secret.ResetPasswordInput(
                code=str(uuid.UUID('{12345678-1234-5678-1234-567812345678}')),
                password='',
            )
