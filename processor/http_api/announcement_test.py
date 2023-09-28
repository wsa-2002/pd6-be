import unittest
from datetime import datetime

from base import enum, do, popo
from util import mock, security, model
from util.model import FilterOperator
import exceptions as exc

from . import announcement


class TestAddAnnouncement(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.post_time = datetime(2023, 7, 20, 1, 1, 1)
        self.expire_time = datetime(2023, 8, 20, 1, 1, 1)

        self.input_data = announcement.AddAnnouncementInput(
            title='test',
            content='test',
            author_id=1,
            post_time=self.post_time,
            expire_time=self.expire_time,
        )
        self.add_result = model.AddOutput(id=1)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_announcement = controller.mock_module('persistence.database.announcement')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_announcement.async_func('add').call_with(
                title=self.input_data.title,
                content=self.input_data.content,
                author_id=self.input_data.author_id,
                post_time=self.input_data.post_time,
                expire_time=self.input_data.expire_time,
            ).returns(1)

            result = await mock.unwrap(announcement.add_announcement)(data=self.input_data)

        self.assertEqual(result, self.add_result)

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
                await mock.unwrap(announcement.add_announcement)(data=self.input_data)


class TestBrowseAnnouncement(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.request_time = datetime(2023, 8, 1, 1, 1, 1)
        self.post_time = datetime(2023, 7, 20, 1, 1, 1)
        self.expire_time = datetime(2023, 8, 20, 1, 1, 1)

        self.limit = model.Limit(10)
        self.offset = model.Offset(0)
        self.filter_str = '[["content", "LIKE", "abcd"]]'
        self.sorter_str = '[["id", "DESC"]]'
        self.filters = [popo.Filter(col_name='content', op=FilterOperator.like, value='abcd')]
        self.sorters = [popo.Sorter(col_name='id', order=enum.SortOrder.desc)]

        self.expected_output_data = [
            do.Announcement(
                id=1,
                title='title',
                content='content',
                author_id=1,
                post_time=self.post_time,
                expire_time=self.expire_time,
                is_deleted=False,
            ),
            do.Announcement(
                id=2,
                title='title2',
                content='content2',
                author_id=2,
                post_time=self.post_time,
                expire_time=self.expire_time,
                is_deleted=False,
            ),
        ]
        self.expected_output_total_count = 2
        self.browse_result = announcement.BrowseAnnouncementOutput(
            data=self.expected_output_data,
            total_count=self.expected_output_total_count,
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_announcement = controller.mock_module('persistence.database.announcement')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('get_system_role').call_with(
                self.login_account.id,
            ).returns(enum.RoleType.manager)

            model_.func('parse_filter').call_with(
                self.filter_str, announcement.BROWSE_ANNOUNCEMENT_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, announcement.BROWSE_ANNOUNCEMENT_COLUMNS,
            ).returns(self.sorters)

            db_announcement.async_func('browse').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
                exclude_scheduled=False,
                ref_time=self.request_time,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(announcement.browse_announcement)(
                limit=self.limit,
                offset=self.offset,
                filter=self.filter_str,
                sort=self.sorter_str,
            )

        self.assertEqual(result, self.browse_result)

    async def test_happy_flow_guest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_announcement = controller.mock_module('persistence.database.announcement')
            model_ = controller.mock_module('util.model')

            service_rbac.async_func('get_system_role').call_with(
                self.login_account.id,
            ).returns(enum.RoleType.guest)

            model_.func('parse_filter').call_with(
                self.filter_str, announcement.BROWSE_ANNOUNCEMENT_COLUMNS,
            ).returns(self.filters)
            model_.func('parse_sorter').call_with(
                self.sorter_str, announcement.BROWSE_ANNOUNCEMENT_COLUMNS,
            ).returns(self.sorters)

            db_announcement.async_func('browse').call_with(
                limit=self.limit,
                offset=self.offset,
                filters=self.filters,
                sorters=self.sorters,
                exclude_scheduled=True,
                ref_time=self.request_time,
            ).returns((self.expected_output_data, self.expected_output_total_count))

            result = await mock.unwrap(announcement.browse_announcement)(
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
            ).returns(None)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(announcement.browse_announcement)(
                    limit=self.limit,
                    offset=self.offset,
                    filter=self.filter_str,
                    sort=self.sorter_str,
                )


class TestReadAnnouncement(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.request_time = datetime(2023, 8, 1, 1, 1, 1)
        self.post_time = datetime(2023, 7, 20, 1, 1, 1)
        self.expire_time = datetime(2023, 8, 20, 1, 1, 1)

        self.announcement_id = 1

        self.expected_output_data = do.Announcement(
            id=1,
            title='title',
            content='content',
            author_id=1,
            post_time=self.post_time,
            expire_time=self.expire_time,
            is_deleted=False,
        )

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_announcement = controller.mock_module('persistence.database.announcement')

            service_rbac.async_func('get_system_role').call_with(
                self.login_account.id,
            ).returns(enum.RoleType.manager)
            db_announcement.async_func('read').call_with(
                1,
                exclude_scheduled=False,
                ref_time=self.request_time,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(announcement.read_announcement)(
                announcement_id=self.announcement_id,
            )

        self.assertEqual(result, self.expected_output_data)

    async def test_happy_flow_guest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_announcement = controller.mock_module('persistence.database.announcement')

            service_rbac.async_func('get_system_role').call_with(
                self.login_account.id,
            ).returns(enum.RoleType.guest)
            db_announcement.async_func('read').call_with(
                1,
                exclude_scheduled=True,
                ref_time=self.request_time,
            ).returns(self.expected_output_data)

            result = await mock.unwrap(announcement.read_announcement)(
                announcement_id=self.announcement_id,
            )

        self.assertEqual(result, self.expected_output_data)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('get_system_role').call_with(
                self.login_account.id,
            ).returns(None)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(announcement.read_announcement)(
                    announcement_id=self.announcement_id,
                )


class TestEditAnnouncement(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.post_time = datetime(2023, 7, 20, 1, 1, 1)
        self.expire_time = datetime(2023, 8, 20, 1, 1, 1)

        self.announcement_id = 1

        self.input_data = announcement.EditAnnouncementInput(
            title='test',
            content='test',
            post_time=self.post_time,
            expire_time=self.expire_time,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_announcement = controller.mock_module('persistence.database.announcement')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_announcement.async_func('edit').call_with(
                announcement_id=self.announcement_id,
                title=self.input_data.title,
                content=self.input_data.content,
                post_time=self.input_data.post_time,
                expire_time=self.input_data.expire_time,
            ).returns(None)

            result = await mock.unwrap(announcement.edit_announcement)(
                announcement_id=self.announcement_id,
                data=self.input_data,
            )

        self.assertIsNone(result)

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
                await mock.unwrap(announcement.edit_announcement)(
                    announcement_id=self.announcement_id,
                    data=self.input_data,
                )


class TestDeleteAnnouncement(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')

        self.announcement_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_announcement = controller.mock_module('persistence.database.announcement')

            service_rbac.async_func('validate_system').call_with(
                self.login_account.id, enum.RoleType.manager,
            ).returns(True)
            db_announcement.async_func('delete').call_with(
                announcement_id=self.announcement_id,
            ).returns(None)

            result = await mock.unwrap(announcement.delete_announcement)(
                announcement_id=self.announcement_id,
            )

        self.assertIsNone(result)

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
                await mock.unwrap(announcement.delete_announcement)(
                    announcement_id=self.announcement_id,
                )
