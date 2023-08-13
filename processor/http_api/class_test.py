import copy
import datetime
import unittest
import uuid

import base.popo
from base import enum, do
import exceptions as exc
from util import model
from util import mock, security

from . import class_


class TestBrowseClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.filter = None
        self.filters = []

        self.sorter = None
        self.sorters = []

        self.limit = model.Limit(50)
        self.offset = model.Offset(0)

        self.classes = [
            do.Class(
                id=1,
                name='test1',
                course_id=1,
                is_deleted=False),
            do.Class(
                id=2,
                name='test2',
                course_id=2,
                is_deleted=False),
            do.Class(
                id=3,
                name='test1-2',
                course_id=1,
                is_deleted=False),
        ]
        self.total_count = len(self.classes)
        self.result = model.BrowseOutputBase(data=self.classes, total_count=self.total_count)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('processor.http_api.class_.model')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)

            model_.func('parse_filter').call_with(self.filter, class_.BROWSE_CLASS_COLUMNS).returns(
                self.filters,
            )
            model_.func('parse_sorter').call_with(self.sorter, class_.BROWSE_CLASS_COLUMNS).returns(
                self.sorters,
            )
            db_class.async_func('browse_with_filter').call_with(
                limit=self.limit, offset=self.offset,
                filters=self.filters, sorters=self.sorters,
            ).returns(
                (self.classes, self.total_count)
            )

            model_.func('BrowseOutputBase').call_with(self.classes, total_count=self.total_count).returns(self.result)

            result = await mock.unwrap(class_.browse_class)(limit=self.limit, offset=self.offset, filter=self.filter,
                                                            sort=self.sorter)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            await mock.unwrap(class_.browse_class)(limit=self.limit, offset=self.offset, filter=self.filter,
                                                   sort=self.sorter)


class TestReadClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.class_ = do.Class(
            id=1,
            name='test',
            course_id=1,
            is_deleted=False,
        )
        self.result = copy.deepcopy(self.class_)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            db_class.async_func('read').call_with(class_id=self.class_id).returns(
                self.class_,
            )

            result = await mock.unwrap(class_.read_class)(class_id=self.class_id)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            await mock.unwrap(class_.read_class)(class_id=self.class_id)


class TestEditClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.data = class_.EditClassInput(
            name='test',
            course_id=1,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            db_class.async_func('edit').call_with(
                class_id=self.class_id,
                name=self.data.name,
                course_id=self.data.course_id,
            ).returns(None)

            result = await mock.unwrap(class_.edit_class)(class_id=self.class_id, data=self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            await mock.unwrap(class_.edit_class)(class_id=self.class_id, data=self.data)


class TestDeleteClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            db_class.async_func('delete').call_with(self.class_id).returns(None)

            result = await mock.unwrap(class_.delete_class)(class_id=self.class_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(False)

            await mock.unwrap(class_.delete_class)(class_id=self.class_id)


class TestBrowseClassMember(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1

        self.filter = None
        self.filters_default = []
        self.filters_self = copy.deepcopy(self.filters_default)
        self.filters_self.append(base.popo.Filter(
            col_name='class_id',
            op=enum.FilterOperator.eq,
            value=self.class_id))

        self.sorter = None
        self.sorters = []

        self.limit = model.Limit(50)
        self.offset = model.Offset(0)

        self.members = [
            do.ClassMember(
                member_id=1,
                class_id=1,
                role=enum.RoleType.normal,
            ),
            do.ClassMember(
                member_id=2,
                class_id=1,
                role=enum.RoleType.normal,
            ),
        ]
        self.accounts = [
            do.Account(
                id=1,
                username='test1',
                nickname='test1',
                real_name='test1',
                role=enum.RoleType.normal,
                is_deleted=False,
                alternative_email=None),
            do.Account(
                id=2,
                username='test2',
                nickname='test2',
                real_name='test2',
                role=enum.RoleType.normal,
                is_deleted=False,
                alternative_email=None),
        ]
        self.student_cards = [
            do.StudentCard(
                id=1,
                institute_id=1,
                student_id='id1',
                email='test1@email.com',
                is_default=True),
            do.StudentCard(
                id=2,
                institute_id=2,
                student_id='id2',
                email='test2@email.com',
                is_default=True),
        ]
        self.institutes = [
            do.Institute(
                id=1,
                abbreviated_name='test',
                full_name='test only',
                email_domain='email.com',
                is_disabled=False),
            do.Institute(
                id=1,
                abbreviated_name='test',
                full_name='test only',
                email_domain='email.com',
                is_disabled=False),
        ]
        self.total_count = len(self.members)
        self.data_result = []
        for i in range(self.total_count):
            self.data_result.append((self.members[i], self.accounts[i], self.student_cards[i], self.institutes[i]))
        self.result = model.BrowseOutputBase(
            data=[class_.BrowseClassMemberOutput(member_id=1,
                                                 role=enum.RoleType.normal,
                                                 username='test1',
                                                 real_name='test1',
                                                 student_id='id1',
                                                 institute_abbreviated_name='test'),
                  class_.BrowseClassMemberOutput(member_id=2,
                                                 role=enum.RoleType.normal,
                                                 username='test2',
                                                 real_name='test2',
                                                 student_id='id2',
                                                 institute_abbreviated_name='test')], total_count=2)

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('processor.http_api.class_.model')
            db_class_vo = controller.mock_module('persistence.database.class_vo')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(True)
            model_.func('parse_filter').call_with(self.filter, class_.BROWSE_CLASS_MEMBER_COLUMNS).returns(
                self.filters_default,
            )
            model_.func('parse_sorter').call_with(self.sorter, class_.BROWSE_CLASS_MEMBER_COLUMNS).returns(
                self.sorters,
            )
            db_class_vo.async_func('browse_member_account_with_student_card_and_institute').call_with(
                limit=self.limit, offset=self.offset, filters=self.filters_self, sorters=self.sorters,
            ).returns(
                (self.data_result, self.total_count),
            )

            model_.func('BrowseOutputBase').call_with(self.result.data, total_count=self.total_count).returns(
                self.result)

            result = await mock.unwrap(class_.browse_class_member)(
                class_id=self.class_id,
                limit=self.limit, offset=self.offset,
                filter=self.filter, sort=self.sorter)

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('processor.http_api.class_.model')
            db_class_vo = controller.mock_module('persistence.database.class_vo')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(False)
            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            model_.func('parse_filter').call_with(self.filter, class_.BROWSE_CLASS_MEMBER_COLUMNS).returns(
                self.filters_default,
            )
            model_.func('parse_sorter').call_with(self.sorter, class_.BROWSE_CLASS_MEMBER_COLUMNS).returns(
                self.sorters,
            )
            db_class_vo.async_func('browse_member_account_with_student_card_and_institute').call_with(
                limit=self.limit, offset=self.offset, filters=self.filters_self, sorters=self.sorters,
            ).returns(
                (self.data_result, self.total_count),
            )

            model_.func('BrowseOutputBase').call_with(self.result.data, total_count=self.total_count).returns(
                self.result)

            result = await mock.unwrap(class_.browse_class_member)(
                class_id=self.class_id,
                limit=self.limit, offset=self.offset,
                filter=self.filter, sort=self.sorter)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(False)
            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            await mock.unwrap(class_.browse_class_member)(
                class_id=self.class_id,
                limit=self.limit, offset=self.offset,
                filter=self.filter, sort=self.sorter)


class TestBrowseAllClassMemberWithAccountReferral(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.members = [
            (do.ClassMember(
                member_id=1,
                class_id=1,
                role=enum.RoleType.normal,
            ), 'test1'),
            (do.ClassMember(
                member_id=2,
                class_id=1,
                role=enum.RoleType.normal,
            ), 'test2'),
            (do.ClassMember(
                member_id=3,
                class_id=1,
                role=enum.RoleType.normal,
            ), 'test3'),
        ]
        self.result = [
            class_.ReadClassMemberOutput(
                member_id=1,
                member_referral='test1',
                member_role=enum.RoleType.normal,
            ),
            class_.ReadClassMemberOutput(
                member_id=2,
                member_referral='test2',
                member_role=enum.RoleType.normal,
            ),
            class_.ReadClassMemberOutput(
                member_id=3,
                member_referral='test3',
                member_role=enum.RoleType.normal,
            ),
        ]

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class_vo = controller.mock_module('persistence.database.class_vo')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(True)
            db_class_vo.async_func('browse_class_member_with_account_referral').call_with(
                class_id=self.class_id,
            ).returns(
                self.members,
            )

            result = await mock.unwrap(class_.browse_all_class_member_with_account_referral)(self.class_id)

        self.assertCountEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class_vo = controller.mock_module('persistence.database.class_vo')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(False)
            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            db_class_vo.async_func('browse_class_member_with_account_referral').call_with(
                class_id=self.class_id,
            ).returns(
                self.members,
            )

            result = await mock.unwrap(class_.browse_all_class_member_with_account_referral)(self.class_id)

        self.assertCountEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(False)
            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            await mock.unwrap(class_.browse_all_class_member_with_account_referral)(self.class_id)


class TestReplaceClassMembers(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.data = [
            class_.SetClassMemberInput(
                account_referral='test1',
                role=enum.RoleType.normal,
            ),
            class_.SetClassMemberInput(
                account_referral='test2',
                role=enum.RoleType.normal,
            ),
            class_.SetClassMemberInput(
                account_referral='test3',
                role=enum.RoleType.normal,
            ),
        ]
        self.member_roles = [(member.account_referral, member.role) for member in self.data]
        self.cm_after = set([data.account_referral for data in self.data])
        self.email_after = {'test1@email.com', 'test2@email.com', 'test3@email.com'}
        self.cm_before_same = copy.deepcopy(self.cm_after)
        self.email_before_same = copy.deepcopy(self.email_after)
        self.cm_before_diff = set('test0')
        self.email_before_diff = set('test1@email.com')
        self.result = [True, True, True]
        self.class_ = do.Class(
            id=1,
            name='test',
            course_id=1,
            is_deleted=False,
        )
        self.course = do.Course(
            id=1,
            name='test',
            type=enum.CourseType.lesson,
            is_deleted=False,
        )
        self.operator = do.Account(
            id=self.login_account.id,
            username=self.login_account.cached_username,
            nickname=self.login_account.cached_username,
            real_name=self.login_account.cached_username,
            role=enum.RoleType.manager,
            is_deleted=False,
            alternative_email=None,
        )

    async def test_happy_flow_unchanged(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            db_class.async_func('browse_member_referrals').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.cm_before_same,
            )
            db_class.async_func('browse_member_emails').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.email_before_same,
            )

            db_class.async_func('replace_members').call_with(
                class_id=self.class_id, member_roles=self.member_roles,
            ).returns(
                self.result,
            )

            db_class.async_func('browse_member_referrals').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.cm_after,
            )
            db_class.async_func('browse_member_emails').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.email_after,
            )

            result = await mock.unwrap(class_.replace_class_members)(self.class_id, self.data)

        self.assertCountEqual(result, self.result)

    async def test_happy_flow_changed(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')
            db_course = controller.mock_module('persistence.database.course')
            db_account = controller.mock_module('persistence.database.account')
            email_notification = controller.mock_module('processor.http_api.class_.email.notification')

            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            db_class.async_func('browse_member_referrals').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.cm_before_diff,
            )
            db_class.async_func('browse_member_emails').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.email_before_diff,
            )

            db_class.async_func('replace_members').call_with(
                class_id=self.class_id, member_roles=self.member_roles,
            ).returns(
                self.result,
            )

            db_class.async_func('browse_member_referrals').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.cm_after,
            )
            db_class.async_func('browse_member_emails').call_with(
                class_id=self.class_id, role=enum.RoleType.manager,
            ).returns(
                self.email_after,
            )

            db_class.async_func('read').call_with(class_id=self.class_id).returns(self.class_)
            db_course.async_func('read').call_with(course_id=self.class_.course_id).returns(self.course)
            db_account.async_func('read').call_with(account_id=context.account.id).returns(self.operator)
            email_notification.async_func('notify_cm_change').call_with(
                tos=(self.email_after | self.email_before_diff),
                added_account_referrals=self.cm_after.difference(self.cm_before_diff),
                removed_account_referrals=self.cm_before_diff.difference(self.cm_after),
                class_name=self.class_.name,
                course_name=self.course.name,
                operator_name=self.operator.username,
            ).returns(None)

            result = await mock.unwrap(class_.replace_class_members)(self.class_id, self.data)

        self.assertCountEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_inherit').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            await mock.unwrap(class_.replace_class_members)(self.class_id, self.data)


class TestDeleteClassMember(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.member_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            db_class.async_func('delete_member').call_with(class_id=self.class_id, member_id=self.member_id).returns(
                None)

            result = await mock.unwrap(class_.delete_class_member)(class_id=self.class_id, member_id=self.member_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            await mock.unwrap(class_.delete_class_member)(class_id=self.class_id, member_id=self.member_id)


class TestAddTeamUnderClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.data = class_.AddTeamInput(
            name='team',
            label='test',
        )
        self.team_id = 1
        self.result = model.AddOutput(
            id=self.team_id,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            db_team.async_func('add').call_with(
                name=self.data.name,
                class_id=self.class_id,
                label=self.data.label,
            ).returns(
                self.team_id,
            )

            result = await mock.unwrap(class_.add_team_under_class)(class_id=self.class_id, data=self.data)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            await mock.unwrap(class_.add_team_under_class)(class_id=self.class_id, data=self.data)


class TestBrowseTeamUnderClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1

        self.filter = None
        self.filters = []
        self.filters_self = copy.deepcopy(self.filters)
        self.filters_self.append(base.popo.Filter(col_name='class_id',
                                                  op=enum.FilterOperator.eq,
                                                  value=self.class_id))

        self.sorter = None
        self.sorters = []

        self.limit = model.Limit(50)
        self.offset = model.Offset(0)

        self.teams = [
            do.Team(
                id=1,
                name='test1',
                class_id=1,
                label='test',
                is_deleted=False),
            do.Team(
                id=2,
                name='test2',
                class_id=1,
                label='test',
                is_deleted=False),
            do.Team(
                id=3,
                name='test3',
                class_id=1,
                label='test',
                is_deleted=False),
        ]
        self.total_count = len(self.teams)
        self.result = model.BrowseOutputBase(data=self.teams, total_count=self.total_count)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('processor.http_api.class_.model')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(True)

            model_.func('parse_filter').call_with(self.filter, class_.BROWSE_TEAM_UNDER_CLASS_COLUMNS).returns(
                self.filters,
            )
            model_.func('parse_sorter').call_with(self.sorter, class_.BROWSE_TEAM_UNDER_CLASS_COLUMNS).returns(
                self.sorters,
            )
            db_team.async_func('browse').call_with(
                limit=self.limit, offset=self.offset,
                filters=self.filters_self, sorters=self.sorters,
            ).returns(
                (self.teams, self.total_count)
            )

            model_.func('BrowseOutputBase').call_with(self.teams, total_count=self.total_count).returns(self.result)

            result = await mock.unwrap(class_.browse_team_under_class)(class_id=self.class_id,
                                                                       limit=self.limit, offset=self.offset,
                                                                       filter=self.filter, sort=self.sorter)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(False)

            await mock.unwrap(class_.browse_team_under_class)(class_id=self.class_id,
                                                              limit=self.limit, offset=self.offset,
                                                              filter=self.filter, sort=self.sorter)


class TestBrowseSubmissionUnderClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.today = datetime.datetime(2023, 4, 9)
        self.class_id = 1

        self.filter = None
        self.filters = []
        self.filters_self = copy.deepcopy(self.filters)
        self.filters_self.append(base.popo.Filter(col_name='class_id',
                                                  op=enum.FilterOperator.eq,
                                                  value=self.class_id))

        self.sorter = None
        self.sorters = []

        self.limit = model.Limit(50)
        self.offset = model.Offset(0)

        self.submissions = [
            do.Submission(
                id=1,
                account_id=1,
                problem_id=1,
                language_id=1,
                content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
                content_length=1,
                filename='test',
                submit_time=self.today),
            do.Submission(
                id=1,
                account_id=1,
                problem_id=1,
                language_id=1,
                content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
                content_length=1,
                filename='test',
                submit_time=self.today),
            do.Submission(
                id=1,
                account_id=1,
                problem_id=1,
                language_id=1,
                content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
                content_length=1,
                filename='test',
                submit_time=self.today),
        ]
        self.total_count = len(self.submissions)
        self.result = model.BrowseOutputBase(data=self.submissions, total_count=self.total_count)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            model_ = controller.mock_module('processor.http_api.class_.model')
            db_submission = controller.mock_module('persistence.database.submission')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter, class_.BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter, class_.BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS
            ).returns(self.sorters)
            db_submission.async_func('browse_under_class').call_with(
                class_id=self.class_id,
                limit=self.limit, offset=self.offset,
                filters=self.filters, sorters=self.sorters,
            ).returns(
                (self.submissions, self.total_count),
            )

            model_.func('BrowseOutputBase').call_with(self.submissions, total_count=self.total_count).returns(
                self.result)

            result = await mock.unwrap(class_.browse_submission_under_class)(class_id=self.class_id,
                                                                             limit=self.limit, offset=self.offset,
                                                                             filter=self.filter,
                                                                             sort=self.sorter)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
            self.assertRaises(exc.NoPermission),
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)

            await mock.unwrap(class_.browse_submission_under_class)(class_id=self.class_id,
                                                                    limit=self.limit, offset=self.offset,
                                                                    filter=self.filter,
                                                                    sort=self.sorter)
