from copy import deepcopy
from datetime import datetime
import unittest
from uuid import UUID

from fastapi import UploadFile

import exceptions as exc
from base import enum, do, popo
from util import mock, model, security

from . import grade


class TestImportClassGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.request_time = datetime(2023, 7, 29, 12)

        self.class_id = 1
        self.title = "title"
        self.grade_file = UploadFile(filename="filename")

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            service_csv = controller.mock_module('service.csv')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                class_id=self.class_id,
            ).returns(True)
            service_csv.async_func('import_class_grade').call_with(
                grade_file=mock.AnyInstanceOf(type(self.grade_file.file)), class_id=self.class_id,
                title=self.title, update_time=context.request_time,
            ).returns(None)

            result = await mock.unwrap(grade.import_class_grade)(self.class_id, self.title, self.grade_file)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                class_id=self.class_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.import_class_grade)(self.class_id, self.title, self.grade_file)


class TestAddGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.request_time = datetime(2023, 7, 29, 12)

        self.class_id = 1
        self.grade_id = 1
        self.data = grade.AddGradeInput(
            receiver_referral="receiver",
            grader_referral="grader",
            title="title",
            score="score",
            comment="comment",
        )

        self.expected_happy_flow_result = model.AddOutput(id=self.grade_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                class_id=self.class_id,
            ).returns(True)
            db_grade.async_func('add').call_with(
                receiver=self.data.receiver_referral, grader=self.data.grader_referral,
                class_id=self.class_id, title=self.data.title, score=self.data.score,
                comment=self.data.comment, update_time=context.request_time,
            ).returns(self.grade_id)

            result = await mock.unwrap(grade.add_grade)(self.class_id, self.data)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                class_id=self.class_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.add_grade)(self.class_id, self.data)


class TestBrowseClassGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.class_id = 1
        self.limit = model.Limit(20)
        self.offset = model.Offset(0)
        self.filter_str = '[["content", "LIKE", "abcd"]]'
        self.sorter_str = '[]'

        self.BROWSE_CLASS_GRADE_COLUMNS = grade.BROWSE_CLASS_GRADE_COLUMNS
        self.filters = [popo.Filter(col_name='content', op=enum.FilterOperator.like, value='abcd')]
        self.filters_before_append = deepcopy(self.filters)
        self.filters.append(popo.Filter(col_name='class_id',
                                        op=enum.FilterOperator.eq,
                                        value=self.class_id))
        self.filters_manager = deepcopy(self.filters)
        self.filters_normal = deepcopy(self.filters)
        self.filters_normal.append(popo.Filter(col_name='receiver_id',
                                               op=enum.FilterOperator.eq,
                                               value=self.account.id))
        self.sorters = []

        self.grades = [
            do.Grade(
                id=1,
                receiver_id=1,
                grader_id=1,
                class_id=1,
                title="title",
                score="score",
                comment="comment",
                update_time=datetime(2023, 7, 29),
                is_deleted=False,
            ),
            do.Grade(
                id=2,
                receiver_id=1,
                grader_id=1,
                class_id=1,
                title="title",
                score="score",
                comment="comment",
                update_time=datetime(2023, 7, 29),
                is_deleted=False,
            ),
        ]
        self.total_count = 2

        self.expected_happy_flow_result = grade.BrowseClassGradeOutput(self.grades, total_count=self.total_count)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, class_id=self.class_id,
            ).returns(enum.RoleType.manager)
            controller.mock_global_func('util.model.parse_filter').call_with(
                self.filter_str, grade.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.filters_before_append)
            controller.mock_global_func('util.model.parse_sorter').call_with(
                self.sorter_str, grade.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.sorters)
            db_grade.async_func('browse').call_with(
                limit=self.limit, offset=self.offset,
                filters=self.filters_manager, sorters=self.sorters,
            ).returns(
                (self.grades, self.total_count),
            )

            result = await mock.unwrap(grade.browse_class_grade)(self.class_id, self.limit, self.offset,
                                                                 self.filter_str, self.sorter_str)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, class_id=self.class_id,
            ).returns(enum.RoleType.normal)
            controller.mock_global_func('util.model.parse_filter').call_with(
                self.filter_str, grade.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.filters_before_append)
            controller.mock_global_func('util.model.parse_sorter').call_with(
                self.sorter_str, grade.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.sorters)
            db_grade.async_func('browse').call_with(
                limit=self.limit, offset=self.offset,
                filters=self.filters_normal, sorters=self.sorters,
            ).returns(
                (self.grades, self.total_count),
            )

            result = await mock.unwrap(grade.browse_class_grade)(self.class_id, self.limit, self.offset,
                                                                 self.filter_str, self.sorter_str)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, class_id=self.class_id,
            ).returns(enum.RoleType.guest)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.browse_class_grade)(self.class_id, self.limit, self.offset,
                                                            self.filter_str, self.sorter_str)


class TestBrowseAccountGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.account_other = security.AuthedAccount(id=2, cached_username='other')

        self.class_id = 1
        self.limit = model.Limit(20)
        self.offset = model.Offset(0)
        self.filter = '[["content", "LIKE", "abcd"]]'
        self.sort = None

        self.BROWSE_ACCOUNT_GRADE_COLUMNS = grade.BROWSE_ACCOUNT_GRADE_COLUMNS
        self.filters = [popo.Filter(col_name='content', op=enum.FilterOperator.eq, value='abcd')]
        self.filters_before_append = deepcopy(self.filters)
        self.filters.append(popo.Filter(col_name='receiver_id',
                                        op=enum.FilterOperator.eq,
                                        value=self.account.id))
        self.sorters = []

        self.grades = [
            do.Grade(
                id=1,
                receiver_id=1,
                grader_id=1,
                class_id=1,
                title="title",
                score="score",
                comment="comment",
                update_time=datetime(2023, 7, 29),
                is_deleted=False,
            ),
            do.Grade(
                id=2,
                receiver_id=1,
                grader_id=1,
                class_id=1,
                title="title",
                score="score",
                comment="comment",
                update_time=datetime(2023, 7, 29),
                is_deleted=False,
            ),
        ]
        self.total_count = 2

        self.expected_happy_flow_result = grade.BrowseAccountGradeOutput(self.grades, total_count=self.total_count)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            db_grade = controller.mock_module('persistence.database.grade')

            controller.mock_global_func('util.model.parse_filter').call_with(
                self.filter, grade.BROWSE_ACCOUNT_GRADE_COLUMNS,
            ).returns(self.filters_before_append)
            controller.mock_global_func('util.model.parse_sorter').call_with(
                self.sort, grade.BROWSE_ACCOUNT_GRADE_COLUMNS,
            ).returns(self.sorters)
            db_grade.async_func('browse').call_with(
                limit=self.limit, offset=self.offset,
                filters=self.filters, sorters=self.sorters,
            ).returns(
                (self.grades, self.total_count),
            )

            result = await mock.unwrap(grade.browse_account_grade)(self.account.id, self.limit, self.offset,
                                                                   self.filter, self.sort)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Context() as context,
        ):
            context.set_account(self.account)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.browse_account_grade)(self.account_other.id, self.limit,
                                                              self.offset, self.filter, self.sort)


class TestGetGradeTemplateFile(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )
        self.filename = "filename"

        self.expected_happy_flow_result = grade.GetGradeTemplateOutput(
            s3_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            filename=self.filename,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_csv = controller.mock_module('service.csv')
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_csv.async_func('get_grade_template').call_with().returns(
                (self.s3_file, self.filename),
            )

            result = await mock.unwrap(grade.get_grade_template_file)()

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.get_grade_template_file)()


class TestGetGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.account_other = security.AuthedAccount(id=2, cached_username='other')

        self.grade = do.Grade(
            id=1,
            receiver_id=self.account.id,
            grader_id=1,
            class_id=1,
            title="title",
            score="score",
            comment="comment",
            update_time=datetime(2023, 7, 29),
            is_deleted=False,
        )

        self.expected_happy_flow_result = self.grade

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, grade_id=self.grade.id,
            ).returns(enum.RoleType.manager)
            db_grade.async_func('read').call_with(
                grade_id=self.grade.id,
            ).returns(self.grade)

            result = await mock.unwrap(grade.get_grade)(self.grade.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, grade_id=self.grade.id,
            ).returns(enum.RoleType.normal)
            db_grade.async_func('read').call_with(
                grade_id=self.grade.id,
            ).returns(self.grade)

            result = await mock.unwrap(grade.get_grade)(self.grade.id)

        self.assertEqual(result, self.expected_happy_flow_result)

    async def test_no_permission_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account_other)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, grade_id=self.grade.id,
            ).returns(enum.RoleType.normal)
            db_grade.async_func('read').call_with(
                grade_id=self.grade.id,
            ).returns(self.grade)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.get_grade)(self.grade.id)

    async def test_no_permission_guest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account_other)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, grade_id=self.grade.id,
            ).returns(enum.RoleType.guest)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.get_grade)(self.grade.id)


class TestEditGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')

        self.grade_id = 1
        self.request_time = datetime(2023, 7, 29)
        self.data = grade.EditGradeInput(
            title="title",
            score="score",
            comment="comment",
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                grade_id=self.grade_id,
            ).returns(True)
            db_grade.async_func('edit').call_with(
                grade_id=self.grade_id, grader_id=context.account.id,
                title=self.data.title, score=self.data.score,
                comment=self.data.comment, update_time=context.request_time,
            ).returns(None)

            result = await mock.unwrap(grade.edit_grade)(self.grade_id, self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                grade_id=self.grade_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.edit_grade)(self.grade_id, self.data)


class TestDeleteGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='self')
        self.grade_id = 1

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_grade = controller.mock_module('persistence.database.grade')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                grade_id=self.grade_id,
            ).returns(True)
            db_grade.async_func('delete').call_with(self.grade_id).returns(None)

            result = await mock.unwrap(grade.delete_grade)(self.grade_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager,
                grade_id=self.grade_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(grade.delete_grade)(self.grade_id)
