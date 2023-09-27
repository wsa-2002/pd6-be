from copy import deepcopy
import unittest
from datetime import datetime

from base import enum, vo, popo
from util import mock, security, model
from util.model import FilterOperator
import exceptions as exc

from . import view


class TestViewBrowseAccountWithDefaultStudentId(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["account_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=model.FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name="account_id", order=enum.SortOrder.desc)]

        self.expected_output_data = [
            vo.ViewAccount(
                account_id=1,
                username='username',
                real_name='real_name',
                student_id='id',
            ),
            vo.ViewAccount(
                account_id=2,
                username='username2',
                real_name='real_name2',
                student_id='id2',
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewAccountOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_ACCOUNT_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_ACCOUNT_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('account').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_account_with_default_student_id)(
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
                await mock.unwrap(view.view_browse_account_with_default_student_id)(
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewBrowseClassMember(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["account_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=model.FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name="account_id", order=enum.SortOrder.desc)]

        self.filters_after_append = deepcopy(self.filters)
        self.filters_after_append.append(popo.Filter(col_name='class_id',
                                                     op=FilterOperator.eq,
                                                     value=self.class_id))

        self.expected_output_data = [
            vo.ViewClassMember(
                account_id=1,
                username='username',
                student_id='id',
                real_name='real_name',
                abbreviated_name='abbreviated_name',
                role=enum.RoleType.normal,
                class_id=1,
            ),
            vo.ViewClassMember(
                account_id=2,
                username='username2',
                student_id='id2',
                real_name='real_name2',
                abbreviated_name='abbreviated_name2',
                role=enum.RoleType.normal,
                class_id=1,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewClassMemberOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow_normal(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_CLASS_MEMBER_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_CLASS_MEMBER_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('class_member').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters_after_append,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_class_member)(
                class_id=self.class_id,
                limit=self.limit,
                offset=self.offset,
                filter=self.filter_str,
                sort=self.sorter_str,
            )

        self.assertEqual(result, self.browse_result)

    async def test_happy_flow_class_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(False)
            service_rbac.async_func('validate_inherit').call_with(
                self.login_account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_CLASS_MEMBER_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_CLASS_MEMBER_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('class_member').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters_after_append,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_class_member)(
                class_id=self.class_id,
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

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, class_id=self.class_id,
            ).returns(False)
            service_rbac.async_func('validate_inherit').call_with(
                self.login_account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(view.view_browse_class_member)(
                    class_id=self.class_id,
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewBrowseSubmissionUnderClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.submit_time = datetime(2023, 8, 1, 1, 1, 1)

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["account_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=model.FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name="account_id", order=enum.SortOrder.desc)]

        self.expected_output_data = [
            vo.ViewSubmissionUnderClass(
                submission_id=1,
                account_id=1,
                username='username',
                student_id='id',
                real_name='real_name',
                challenge_id=1,
                challenge_title='title',
                problem_id=1,
                challenge_label='label',
                verdict=enum.VerdictType.accepted,
                submit_time=self.submit_time,
                class_id=1,
            ),
            vo.ViewSubmissionUnderClass(
                submission_id=2,
                account_id=2,
                username='username2',
                student_id='id2',
                real_name='real_name2',
                challenge_id=2,
                challenge_title='title2',
                problem_id=2,
                challenge_label='label2',
                verdict=enum.VerdictType.accepted,
                submit_time=self.submit_time,
                class_id=1,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewSubmissionUnderClassOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, class_id=self.class_id
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('class_submission').call_with(
                class_id=self.class_id,
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_submission_under_class)(
                class_id=self.class_id,
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

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(view.view_browse_submission_under_class)(
                    class_id=self.class_id,
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewBrowseSubmission(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')
        self.submit_time = datetime(2023, 8, 1, 1, 1, 1)

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["account_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=model.FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name="account_id", order=enum.SortOrder.desc)]

        self.filters_after_append = deepcopy(self.filters)
        self.filters_after_append.append(popo.Filter(col_name='account_id',
                                                     op=FilterOperator.eq,
                                                     value=self.login_account.id))

        self.expected_output_data = [
            vo.ViewMySubmission(
                submission_id=1,
                course_id=1,
                course_name='course_name',
                class_id=1,
                class_name='class_name',
                challenge_id=1,
                challenge_title='challenge_title',
                problem_id=1,
                challenge_label='challenge_label',
                verdict=enum.VerdictType.accepted,
                submit_time=self.submit_time,
                account_id=1,
            ),
            vo.ViewMySubmission(
                submission_id=2,
                course_id=2,
                course_name='course_name2',
                class_id=2,
                class_name='class_name2',
                challenge_id=2,
                challenge_title='challenge_title2',
                problem_id=2,
                challenge_label='challenge_label2',
                verdict=enum.VerdictType.accepted,
                submit_time=self.submit_time,
                account_id=2,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewMySubmissionOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_SUBMISSION_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_SUBMISSION_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('my_submission').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters_after_append,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_submission)(
                account_id=self.login_account.id,
                limit=self.limit,
                offset=self.offset,
                filter=self.filter_str,
                sort=self.sorter_str,
            )

        self.assertEqual(result, self.browse_result)

    async def test_no_permission(self):
        with (
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(view.view_browse_submission)(
                    account_id=self.login_account.id,
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewBrowseMySubmissionUnderProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='other')
        self.submit_time = datetime(2023, 8, 1, 1, 1, 1)
        self.problem_id = 1

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["score", ">", 80]]'
        self.sorter_str = '[["account_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='score', op=FilterOperator.eq, value=self.login_account.id)]
        self.sorters = [popo.Sorter(col_name='account_id', order=enum.SortOrder.desc)]

        self.filters_after_append = deepcopy(self.filters)
        self.filters_after_append.append(popo.Filter(col_name='account_id',
                                                     op=FilterOperator.eq,
                                                     value=self.login_account.id))
        self.filters_after_append.append(popo.Filter(col_name='problem_id',
                                                     op=FilterOperator.eq,
                                                     value=self.problem_id))

        self.expected_output_data = [
            vo.ViewMySubmissionUnderProblem(
                submission_id=1,
                judgment_id=1,
                verdict=enum.VerdictType.accepted,
                score=100,
                total_time=10,
                max_memory=10,
                submit_time=self.submit_time,
                account_id=1,
                problem_id=1,
            ),
            vo.ViewMySubmissionUnderProblem(
                submission_id=2,
                judgment_id=2,
                verdict=enum.VerdictType.accepted,
                score=100,
                total_time=10,
                max_memory=10,
                submit_time=self.submit_time,
                account_id=1,
                problem_id=1,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewMySubmissionUnderProblemOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('my_submission_under_problem').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters_after_append,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_my_submission_under_problem)(
                account_id=self.login_account.id,
                problem_id=self.problem_id,
                limit=self.limit,
                offset=self.offset,
                filter=self.filter_str,
                sort=self.sorter_str,
            )

        self.assertEqual(result, self.browse_result)

    async def test_no_permission(self):
        with (
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(view.view_browse_my_submission_under_problem)(
                    account_id=self.login_account.id,
                    problem_id=self.problem_id,
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewBrowseProblemSetUnderClass(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.request_time = datetime(2023, 8, 1, 1, 1, 1)

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["challenge_id", "=", 1]]'
        self.sorter_str = '[["challenge_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='challenge_id', op=FilterOperator.eq, value=1)]
        self.sorters = [popo.Sorter(col_name='challenge_id', order=enum.SortOrder.desc)]

        self.filters_after_append = deepcopy(self.filters)
        self.filters_after_append.append(popo.Filter(col_name='class_id',
                                                     op=FilterOperator.eq,
                                                     value=self.class_id))

        self.expected_output_data = [
            vo.ViewProblemSet(
                challenge_id=1,
                challenge_title='challenge_title',
                problem_id=1,
                challenge_label='label',
                problem_title='problem_title',
                class_id=1,
            ),
            vo.ViewProblemSet(
                challenge_id=2,
                challenge_title='challenge_title2',
                problem_id=2,
                challenge_label='label2',
                problem_title='problem_title2',
                class_id=2,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewProblemSetOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('get_system_role').call_with(
                self.login_account.id,
            ).returns(enum.RoleType.normal)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_PROBLEM_SET_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_PROBLEM_SET_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('problem_set').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters_after_append,
                sorters=self.sorters,
                ref_time=self.request_time,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_problem_set_under_class)(
                class_id=self.class_id,
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

            service_rbac.async_func('get_system_role').call_with(
                self.login_account.id,
            ).returns(enum.RoleType.guest)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(view.view_browse_problem_set_under_class)(
                    class_id=self.class_id,
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewBrowseClassGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.update_time = datetime(2023, 8, 1, 1, 1, 1)

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["account_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=model.FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name="account_id", order=enum.SortOrder.desc)]

        self.filters_after_append_manager = deepcopy(self.filters)
        self.filters_after_append_manager.append(popo.Filter(col_name='class_id',
                                                             op=FilterOperator.eq,
                                                             value=self.class_id))

        self.filters_after_append_normal = deepcopy(self.filters)
        self.filters_after_append_normal.append(popo.Filter(col_name='class_id',
                                                            op=FilterOperator.eq,
                                                            value=self.class_id))
        self.filters_after_append_normal.append(popo.Filter(col_name='grade.receiver_id',
                                                            op=FilterOperator.eq,
                                                            value=self.login_account.id))
        self.expected_output_data = [
            vo.ViewGrade(
                account_id=1,
                username='username',
                student_id='id',
                real_name='real_name',
                title='title',
                score='100',
                update_time=self.update_time,
                grade_id=1,
                class_id=1,
            ),
            vo.ViewGrade(
                account_id=1,
                username='username2',
                student_id='id2',
                real_name='real_name2',
                title='title2',
                score='100',
                update_time=self.update_time,
                grade_id=2,
                class_id=1,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewGradeOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.sorters)

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)

            db_view.async_func('grade').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters_after_append_manager,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_class_grade)(
                class_id=self.class_id,
                limit=self.limit,
                offset=self.offset,
                filter=self.filter_str,
                sort=self.sorter_str,
            )

        self.assertEqual(result, self.browse_result)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_CLASS_GRADE_COLUMNS,
            ).returns(self.sorters)

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)
            db_view.async_func('grade').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters_after_append_normal,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_class_grade)(
                class_id=self.class_id,
                limit=self.limit,
                offset=self.offset,
                filter=self.filter_str,
                sort=self.sorter_str,
            )

        self.assertEqual(result, self.browse_result)


class TestViewBrowseAccessLog(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.access_time = datetime(2023, 8, 1, 1, 1, 1)

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["account_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=model.FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name="account_id", order=enum.SortOrder.desc)]

        self.expected_output_data = [
            vo.ViewAccessLog(
                account_id=1,
                username='username',
                student_id='id',
                real_name='real_name',
                ip='ip',
                resource_path='path',
                request_method='method',
                access_time=self.access_time,
                access_log_id=1,
            ),
            vo.ViewAccessLog(
                account_id=1,
                username='username2',
                student_id='id2',
                real_name='real_name2',
                ip='ip2',
                resource_path='path2',
                request_method='method2',
                access_time=self.access_time,
                access_log_id=2,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewAccessLogOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_ACCESS_LOG_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_ACCESS_LOG_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('access_log').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_browse_access_log)(
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
                await mock.unwrap(view.view_browse_access_log)(
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewPeerReviewSummaryReview(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.peer_review_id = 1

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["student_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name='student_id', order=enum.SortOrder.desc)]

        self.expected_output_data = [
            vo.ViewPeerReviewRecord(
                account_id=1,
                username='username',
                student_id='id',
                real_name='real_name',
                peer_review_record_ids=[1, 2],
                peer_review_record_scores=[100, 100],
                average_score=100,
            ),
            vo.ViewPeerReviewRecord(
                account_id=1,
                username='username2',
                student_id='id2',
                real_name='real_name2',
                peer_review_record_ids=[1, 2],
                peer_review_record_scores=[100, 80],
                average_score=90,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewPeerReviewRecordOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager,
                peer_review_id=self.peer_review_id,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_PEER_REVIEW_RECORD_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_PEER_REVIEW_RECORD_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('view_peer_review_record').call_with(
                peer_review_id=self.peer_review_id,
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
                is_receiver=False,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_peer_review_summary_review)(
                peer_review_id=1,
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

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager,
                peer_review_id=self.peer_review_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(view.view_peer_review_summary_review)(
                    peer_review_id=1,
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestViewPeerReviewSummaryReceive(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.peer_review_id = 1

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["username", "LIKE", "abcd"]]'
        self.sorter_str = '[["student_id", "DESC"]]'
        self.filters = [popo.Filter(col_name='username', op=FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name='student_id', order=enum.SortOrder.desc)]

        self.expected_output_data = [
            vo.ViewPeerReviewRecord(
                account_id=1,
                username='username',
                student_id='id',
                real_name='real_name',
                peer_review_record_ids=[1, 2],
                peer_review_record_scores=[100, 100],
                average_score=100,
            ),
            vo.ViewPeerReviewRecord(
                account_id=1,
                username='username2',
                student_id='id2',
                real_name='real_name2',
                peer_review_record_ids=[1, 2],
                peer_review_record_scores=[100, 80],
                average_score=90,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = view.ViewPeerReviewRecordOutput(
            self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_view = controller.mock_module('persistence.database.view')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager,
                peer_review_id=self.peer_review_id,
            ).returns(True)

            model_.func('parse_filter').call_with(
                self.filter_str, view.BROWSE_PEER_REVIEW_RECORD_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, view.BROWSE_PEER_REVIEW_RECORD_COLUMNS,
            ).returns(self.sorters)

            db_view.async_func('view_peer_review_record').call_with(
                peer_review_id=self.peer_review_id,
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
                is_receiver=True,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(view.view_peer_review_summary_receive)(
                peer_review_id=1,
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

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager,
                peer_review_id=self.peer_review_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(view.view_peer_review_summary_receive)(
                    peer_review_id=1,
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )
