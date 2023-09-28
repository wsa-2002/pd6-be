import copy
import unittest
from uuid import UUID

import pydantic

from base import enum, do
from util import mock, security, model
import exceptions as exc

from . import account


class TestBrowseAccountWithDefaultStudentId(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.account = do.Account(
            id=self.login_account.id,
            username="user",
            nickname="nick",
            real_name="real",
            role=enum.RoleType.guest,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.limit = model.Limit(50)
        self.offset = model.Offset(0)
        self.filter_str = '[]'
        self.sorter_str = '[]'
        self.filters = []
        self.sorters = []
        self.expected_output_data = [
            (do.Account(
                id=1,
                username='username1',
                nickname='nickname1',
                real_name='real_name1',
                role=enum.RoleType.manager,
                is_deleted=False,
                alternative_email='alternative1@gmail.com',
            ), do.StudentCard(
                id=1,
                institute_id=1,
                student_id='id1',
                email='email1@gmail.com',
                is_default=True,
            )),
            (do.Account(
                id=2,
                username='username2',
                nickname='nickname2',
                real_name='real_name2',
                role=enum.RoleType.normal,
                is_deleted=False,
                alternative_email='alternative2@gmail.com',
            ), do.StudentCard(
                id=2,
                institute_id=2,
                student_id='id2',
                email='email2@gmail.com',
                is_default=True,
            ))
        ]
        self.expected_output_total_count = 2
        self.browse_result = account.BrowseAccountWithDefaultStudentIdOutput(
            data=[account.BrowseAccountOutput(
                    id=acc.id, username=acc.username, nickname=acc.nickname,
                    role=acc.role, real_name=acc.real_name,
                    alternative_email=acc.alternative_email, student_id=student_card.student_id)
                  for acc, student_card in self.expected_output_data],
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, account.BROWSE_ACCOUNT_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, account.BROWSE_ACCOUNT_COLUMNS,
            ).returns(self.sorters)

            db_account_vo.async_func('browse_with_default_student_card').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(account.browse_account_with_default_student_id)(
                limit=self.limit,
                offset=self.offset,
                filter=self.filter_str,
                sort=self.sorter_str,
            )

        self.assertEqual(result, self.browse_result)

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
                await mock.unwrap(account.browse_account_with_default_student_id)(
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestBatchGetAccountWithDefaultStudentId(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.account_ids_json = "[1, 2]"
        self.account_ids = [1, 2]
        self.empty_account_ids_json = "[]"
        self.empty_account_ids = []

        self.expected_output_data = [
            (do.Account(
                id=1,
                username='username1',
                nickname='nickname1',
                real_name='real_name1',
                role=enum.RoleType.manager,
                is_deleted=False,
                alternative_email='alternative1@gmail.com',
            ), do.StudentCard(
                id=1,
                institute_id=1,
                student_id='id1',
                email='email1@gmail.com',
                is_default=True,
            )),
            (do.Account(
                id=2,
                username='username2',
                nickname='nickname2',
                real_name='real_name2',
                role=enum.RoleType.normal,
                is_deleted=False,
                alternative_email='alternative2@gmail.com',
            ), do.StudentCard(
                id=2,
                institute_id=2,
                student_id='id2',
                email='email2@gmail.com',
                is_default=True,
            ))
        ]
        self.browse_result = [
            account.BatchGetAccountOutput(
                id=acc.id, username=acc.username, real_name=acc.real_name,
                student_id=student_card.student_id)
            for acc, student_card in self.expected_output_data]
        self.empty_result = []

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account_vo = controller.mock_module('persistence.database.account_vo')

            controller.mock_global_func('pydantic.parse_obj_as').call_with(list[int], self.account_ids_json).returns(
                self.account_ids,
            )
            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.normal,
            ).returns(True)

            db_account_vo.async_func('browse_list_with_default_student_card').call_with(
                account_ids=self.account_ids,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(account.batch_get_account_with_default_student_id)(
                account_ids=self.account_ids_json,
            )

        self.assertEqual(result, self.browse_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            controller.mock_global_func('pydantic.parse_obj_as').call_with(list[int], self.account_ids_json).returns(
                self.account_ids,
            )

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.batch_get_account_with_default_student_id)(
                    account_ids=self.account_ids_json,
                )

    async def test_not_account_ids(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                list[int], self.empty_account_ids_json,
            ).returns(self.empty_account_ids)
            result = await mock.unwrap(account.batch_get_account_with_default_student_id)(
                account_ids=self.empty_account_ids_json,
            )

        self.assertEqual(result, self.empty_result)


class TestBatchGetAccountByAccountReferrals(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.account_referrals_json = "['referral1', 'referral2']"
        self.account_referrals = ['referral1', 'referral2']
        self.empty_account_referrals_json = "[]"
        self.empty_account_referrals = []

        self.expected_output_data = [
            (do.Account(
                id=1,
                username='username1',
                nickname='nickname1',
                real_name='real_name1',
                role=enum.RoleType.manager,
                is_deleted=False,
                alternative_email='alternative1@gmail.com',
            ), do.StudentCard(
                id=1,
                institute_id=1,
                student_id='id1',
                email='email1@gmail.com',
                is_default=True,
            )),
            (do.Account(
                id=2,
                username='username2',
                nickname='nickname2',
                real_name='real_name2',
                role=enum.RoleType.normal,
                is_deleted=False,
                alternative_email='alternative2@gmail.com',
            ), do.StudentCard(
                id=2,
                institute_id=2,
                student_id='id2',
                email='email2@gmail.com',
                is_default=True,
            ))
        ]
        self.browse_result = [
            account.BatchGetAccountOutput(
                id=acc.id, username=acc.username, real_name=acc.real_name,
                student_id=student_card.student_id)
            for acc, student_card in self.expected_output_data]
        self.empty_result = []

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account_vo = controller.mock_module('persistence.database.account_vo')

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                list[str], self.account_referrals_json,
            ).returns(self.account_referrals)
            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.normal,
            ).returns(True)

            db_account_vo.async_func('batch_read_by_account_referral').call_with(
                account_referrals=self.account_referrals,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(account.batch_get_account_by_account_referrals)(
                account_referrals=self.account_referrals_json,
            )

        self.assertEqual(result, self.browse_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                list[str], self.account_referrals_json,
            ).returns(self.account_referrals)

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.batch_get_account_by_account_referrals)(
                    account_referrals=self.account_referrals_json,
                )

    async def test_not_account_referrals(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            controller.mock_global_func('pydantic.parse_obj_as').call_with(
                list[int], self.empty_account_referrals_json,
            ).returns(self.empty_account_referrals)
            result = await mock.unwrap(account.batch_get_account_with_default_student_id)(
                account_ids=self.empty_account_referrals_json,
            )

        self.assertEqual(result, self.empty_result)


class TestBrowseAllAccountWithClassRole(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')

        self.expected_output_data = [
            (do.ClassMember(
                class_id=1,
                member_id=1,
                role=enum.RoleType.manager,
            ), do.Class(
                id=1,
                name="class1",
                course_id=1,
                is_deleted=False,
            ), do.Course(
                id=1,
                name='course1',
                type=enum.CourseType.lesson,
                is_deleted=False,
            )),
            (do.ClassMember(
                class_id=2,
                member_id=2,
                role=enum.RoleType.manager,
            ), do.Class(
                id=2,
                name="class2",
                course_id=2,
                is_deleted=False,
            ), do.Course(
                id=2,
                name='course2',
                type=enum.CourseType.lesson,
                is_deleted=False,
            ))
        ]
        self.browse_result = [
            account.BrowseAccountWithRoleOutput(member_id=class_member.member_id,
                                                role=class_member.role,
                                                class_id=class_member.class_id,
                                                class_name=class_.name,
                                                course_id=course.id,
                                                course_name=course.name)
            for class_member, class_, course in self.expected_output_data]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_class = controller.mock_module('persistence.database.class_')

            db_class.async_func('browse_role_by_account_id').call_with(
                account_id=self.login_account.id,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(account.browse_all_account_with_class_role)(
                account_id=self.login_account.id,
            )
        self.assertEqual(result, self.browse_result)

    async def test_no_permission(self):
        with (
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.browse_all_account_with_class_role)(
                    account_id=self.login_account.id,
                )


class TestGetAccountTemplateFile(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'test.csv'

        self.get_result = account.GetAccountTemplateOutput(
            s3_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            filename='test.csv',
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_csv = controller.mock_module('service.csv')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)

            db_csv.async_func('get_account_template').call_with().returns((self.s3_file, self.filename))

            result = await mock.unwrap(account.get_account_template_file)()

        self.assertEqual(result, self.get_result)

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
                await mock.unwrap(account.get_account_template_file)()


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
        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='id1',
            email='email1@gmail.com',
            is_default=True,
        )
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

            result = await mock.unwrap(account.read_account_with_default_student_id)(account_id=self.account.id)

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

            result = await mock.unwrap(account.read_account_with_default_student_id)(account_id=self.account.id)

        self.assertEqual(result, self.result)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account_vo = controller.mock_module('persistence.database.account_vo')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)
            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.normal,
            ).returns(False)
            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=self.account.id,
            ).returns((self.account, self.student_card))

            result = await mock.unwrap(account.read_account_with_default_student_id)(account_id=self.account.id)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.manager,
            ).returns(False)
            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.read_account_with_default_student_id)(
                    account_id=self.account.id,
                )


class TestEditAccount(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_login_account = security.AuthedAccount(id=2, cached_username='other')
        self.account = do.Account(
            id=self.login_account.id,
            username="self",
            nickname="nick",
            real_name="real",
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email="alternative",
        )
        self.input_email_add = account.EditAccountInput(
            username='self',
            nickname='self',
            alternative_email='test@example.com',
        )
        self.input_email_default = account.EditAccountInput(
            username='self',
            nickname='self',
        )
        self.input_email_delete = account.EditAccountInput(
            username='self',
            nickname='self',
            alternative_email=None,
        )
        self.code = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')

            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_account.async_func('edit').call_with(
                account_id=self.login_account.id,
                username=self.input_email_default.username,
                nickname=self.input_email_default.nickname,
                real_name=self.input_email_default.real_name,
            ).returns(None)

            result = await mock.unwrap(account.edit_account)(
                account_id=self.login_account.id,
                data=self.input_email_default,
            )

        self.assertIsNone(result)

    async def test_happy_flow_self_email_default(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)
            db_account.async_func('edit').call_with(
                account_id=self.login_account.id,
                username=self.input_email_default.username,
                nickname=self.input_email_default.nickname,
                real_name=self.input_email_default.real_name,
            ).returns(None)

            result = await mock.unwrap(account.edit_account)(
                account_id=self.login_account.id,
                data=self.input_email_default,
            )

        self.assertIsNone(result)

    async def test_happy_flow_self_change_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')
            email_verification = controller.mock_module('persistence.email.verification')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)
            db_account.async_func('add_email_verification').call_with(
                email=self.input_email_add.alternative_email,
                account_id=self.login_account.id,
            ).returns(self.code)
            db_account.async_func('read').call_with(self.login_account.id).returns(self.account)
            email_verification.async_func('send').call_with(
                to=self.input_email_add.alternative_email,
                code=self.code,
                username=self.account.username,
            ).returns(None)

            db_account.async_func('edit').call_with(
                account_id=self.login_account.id,
                username=self.input_email_default.username,
                nickname=self.input_email_default.nickname,
                real_name=self.input_email_default.real_name,
            ).returns(None)

            result = await mock.unwrap(account.edit_account)(
                account_id=self.login_account.id,
                data=self.input_email_add,
            )

        self.assertIsNone(result)

    async def test_happy_flow_self_delete_email(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_account = controller.mock_module('persistence.database.account')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)
            db_account.async_func('delete_alternative_email_by_id').call_with(
                account_id=self.login_account.id,
            ).returns(None)

            db_account.async_func('edit').call_with(
                account_id=self.login_account.id,
                username=self.input_email_default.username,
                nickname=self.input_email_default.nickname,
                real_name=self.input_email_default.real_name,
            ).returns(None)

            result = await mock.unwrap(account.edit_account)(
                account_id=self.login_account.id,
                data=self.input_email_delete,
            )

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.other_login_account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.edit_account)(
                    account_id=self.login_account.id,
                    data=self.input_email_default,
                )

    async def test_invalid_username(self):
        with self.assertRaises(pydantic.ValidationError):
            self.data = account.EditAccountInput(
                username='',
                nickname='self',
                alternative_email='test@example.com',
            )


class TestDeleteAccount(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_account = controller.mock_module('persistence.database.account')
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(True)

            db_account.async_func('delete').call_with(
                account_id=self.login_account.id,
            ).returns(None)

            result = await mock.unwrap(account.delete_account)(
                account_id=self.login_account.id,
            )

        self.assertIsNone(result)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_account = controller.mock_module('persistence.database.account')
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_account.async_func('delete').call_with(
                account_id=self.login_account.id,
            ).returns(None)

            result = await mock.unwrap(account.delete_account)(
                account_id=self.login_account.id,
            )

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(False)
            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.delete_account)(
                    account_id=self.login_account.id,
                )


class TestMakeStudentCardDefault(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')

        self.input = account.DefaultStudentCardInput(
            student_card_id=self.login_account.id
        )
        self.owner_id = self.login_account.id
        self.owner_id_not_belong = self.other_account.id

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_account = controller.mock_module('persistence.database.account')
            db_student_card = controller.mock_module('persistence.database.student_card')
            service_rbac = controller.mock_module('service.rbac')

            db_student_card.async_func('read_owner_id').call_with(
                student_card_id=self.input.student_card_id,
            ).returns(self.owner_id)

            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(True)

            db_account.async_func('edit_default_student_card').call_with(
                account_id=self.login_account.id,
                student_card_id=self.input.student_card_id,
            ).returns(None)

            result = await mock.unwrap(account.make_student_card_default)(
                account_id=self.login_account.id,
                data=self.input,
            )

        self.assertIsNone(result)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_account = controller.mock_module('persistence.database.account')
            db_student_card = controller.mock_module('persistence.database.student_card')
            service_rbac = controller.mock_module('service.rbac')

            db_student_card.async_func('read_owner_id').call_with(
                student_card_id=self.input.student_card_id,
            ).returns(self.owner_id)

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_account.async_func('edit_default_student_card').call_with(
                account_id=self.login_account.id,
                student_card_id=self.input.student_card_id,
            ).returns(None)

            result = await mock.unwrap(account.make_student_card_default)(
                account_id=self.login_account.id,
                data=self.input,
            )

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_student_card = controller.mock_module('persistence.database.student_card')
            service_rbac = controller.mock_module('service.rbac')

            db_student_card.async_func('read_owner_id').call_with(
                student_card_id=self.input.student_card_id,
            ).returns(self.owner_id)

            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.make_student_card_default)(
                    account_id=self.login_account.id,
                    data=self.input,
                )

    async def test_student_card_does_not_belong(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_student_card = controller.mock_module('persistence.database.student_card')

            db_student_card.async_func('read_owner_id').call_with(
                student_card_id=self.input.student_card_id,
            ).returns(self.owner_id_not_belong)

            with self.assertRaises(exc.account.StudentCardDoesNotBelong):
                await mock.unwrap(account.make_student_card_default)(
                    account_id=self.login_account.id,
                    data=self.input,
                )


class TestBrowseAllAccountPendingEmailVerification(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')

        self.output = [
            do.EmailVerification(
                id=1,
                email='email1@gmail.com',
                account_id=1,
                institute_id=1,
                student_id='id1',
                is_consumed=True,
            ), do.EmailVerification(
                id=2,
                email='email1@gmail.com',
                account_id=1,
                institute_id=1,
                student_id='id2',
                is_consumed=True,
            )]

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_email_verification = controller.mock_module('persistence.database.email_verification')
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(True)

            db_email_verification.async_func('browse').call_with(
                account_id=self.login_account.id,
            ).returns(self.output)

            result = await mock.unwrap(account.browse_all_account_pending_email_verification)(
                account_id=self.login_account.id,
            )

        self.assertEqual(result, self.output)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_email_verification = controller.mock_module('persistence.database.email_verification')
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(False)

            db_email_verification.async_func('browse').call_with(
                account_id=self.login_account.id,
            ).returns(self.output)

            result = await mock.unwrap(account.browse_all_account_pending_email_verification)(
                account_id=self.login_account.id,
            )

        self.assertEqual(result, self.output)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                self.other_account.id, enum.RoleType.manager,
            ).returns(False)
            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(account.browse_all_account_pending_email_verification)(
                    account_id=self.login_account.id,
                )
