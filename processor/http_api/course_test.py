import copy
import unittest

from base import enum, do
from base.enum import CourseType
from util import model
from util import mock, security

from . import course


class TestAddCourse(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.data = course.AddCourseInput(name='test', type=CourseType.lesson)
        self.course_id = 1
        self.result = model.AddOutput(id=self.course_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_course = controller.mock_module('persistence.database.course')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            db_course.async_func('add').call_with(name=self.data.name, course_type=self.data.type).returns(
                self.course_id
            )

            result = await mock.unwrap(course.add_course)(data=self.data)

        self.assertEqual(result, self.result)


class TestReadCourse(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.course_id = 1
        self.course = do.Course(
            id=1,
            name='test',
            type=enum.CourseType.lesson,
            is_deleted=False,
        )
        self.result = copy.deepcopy(self.course)

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_course = controller.mock_module('persistence.database.course')

            service_rbac.async_func('get_system_role').call_with(
                context.account.id
            ).returns(enum.RoleType.normal)
            db_course.async_func('read').call_with(self.course_id).returns(
                self.course
            )

            result = await mock.unwrap(course.read_course)(course_id=self.course_id)

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_course = controller.mock_module('persistence.database.course')

            service_rbac.async_func('get_system_role').call_with(
                context.account.id
            ).returns(enum.RoleType.manager)
            db_course.async_func('read').call_with(self.course_id).returns(
                self.course
            )

            result = await mock.unwrap(course.read_course)(course_id=self.course_id)

        self.assertEqual(result, self.result)


class TestBrowseAllCourse(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.courses = [
            do.Course(
                id=1,
                name='test1',
                type=enum.CourseType.lesson,
                is_deleted=False),
            do.Course(
                id=2,
                name='test2',
                type=enum.CourseType.lesson,
                is_deleted=False),
            do.Course(
                id=1,
                name='test3',
                type=enum.CourseType.lesson,
                is_deleted=False),
        ]
        self.result = copy.deepcopy(self.courses)

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_course = controller.mock_module('persistence.database.course')

            service_rbac.async_func('get_system_role').call_with(
                context.account.id
            ).returns(enum.RoleType.normal)
            db_course.async_func('browse').call_with().returns(
                self.courses
            )

            result = await mock.unwrap(course.browse_all_course)()

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_course = controller.mock_module('persistence.database.course')

            service_rbac.async_func('get_system_role').call_with(
                context.account.id
            ).returns(enum.RoleType.manager)
            db_course.async_func('browse').call_with().returns(
                self.courses
            )

            result = await mock.unwrap(course.browse_all_course)()

        self.assertEqual(result, self.result)


class TestEditCourse(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.data = course.EditCourseInput(name='test', type=CourseType.lesson)
        self.course_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_course = controller.mock_module('persistence.database.course')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_course.async_func('edit').call_with(
                course_id=self.course_id,
                name=self.data.name,
                course_type=self.data.type,
            ).returns(None)

            result = await mock.unwrap(course.edit_course)(course_id=self.course_id, data=self.data)

        self.assertIsNone(result)


class TestDeleteCourse(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.course_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_course = controller.mock_module('persistence.database.course')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_course.async_func('delete').call_with(
                self.course_id,
            ).returns(None)

            result = await mock.unwrap(course.delete_course)(course_id=self.course_id)

        self.assertIsNone(result)


class TestAddClassUnderCourse(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.data = course.AddClassInput(name='test')
        self.course_id = 1
        self.class_id = 2
        self.result = model.AddOutput(id=self.class_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_class.async_func('add').call_with(
                name=self.data.name,
                course_id=self.course_id,
            ).returns(
                self.class_id
            )

            result = await mock.unwrap(course.add_class_under_course)(course_id=self.course_id, data=self.data)

        self.assertEqual(result, self.result)


class TestBrowseAllClassUnderCourse(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.course_id = 1
        self.classes = [
            do.Class(
                id=1,
                name='test1',
                course_id=1,
                is_deleted=False),
            do.Class(
                id=2,
                name='test2',
                course_id=1,
                is_deleted=False),
            do.Class(
                id=1,
                name='test3',
                course_id=1,
                is_deleted=False),
        ]
        self.result = copy.deepcopy(self.classes)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_class = controller.mock_module('persistence.database.class_')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.normal,
            ).returns(True)
            db_class.async_func('browse').call_with(course_id=self.course_id).returns(
                self.classes,
            )

            result = await mock.unwrap(course.browse_all_class_under_course)(course_id=self.course_id)

        self.assertEqual(result, self.result)
