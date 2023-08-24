import datetime
import unittest

from base import enum, do
import exceptions as exc
from util import mock, security, model

from . import system


class TestBrowseAccessLog(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.today = datetime.datetime(2023, 4, 9)
        self.filter = None
        self.filters = []
        self.sorter = None
        self.sorters = []
        self.limit = model.Limit(50)
        self.offset = model.Offset(0)
        self.access_logs = [
            do.AccessLog(
                id=1,
                access_time=self.today-datetime.timedelta(days=1),
                request_method='get',
                resource_path='/login',
                ip='123.123.123.123',
                account_id=1,
            ),
            do.AccessLog(
                id=2,
                access_time=self.today,
                request_method='post',
                resource_path='/login',
                ip='123.456.789.012',
                account_id=None,
            ),
        ]
        self.total_count = len(self.access_logs)
        self.result = system.BrowseAccessLogOutput(self.access_logs, self.total_count)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_access_log = controller.mock_module('persistence.database.access_log')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.manager,
            ).returns(True)
            controller.mock_global_func('util.model.parse_filter').call_with(
                self.filter, system.BROWSE_ACCESS_LOG_COLUMNS,
            ).returns(
                self.filters,
            )
            controller.mock_global_func('util.model.parse_sorter').call_with(
                self.sorter, system.BROWSE_ACCESS_LOG_COLUMNS,
            ).returns(
                self.sorters,
            )
            db_access_log.async_func('browse').call_with(
                limit=self.limit, offset=self.offset, filters=self.filters, sorters=self.sorters,
            ).returns(
                (self.access_logs, self.total_count),
            )

            result = await mock.unwrap(system.browse_access_log)(
                self.limit, self.offset,
                self.filter, self.sorter,
            )

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
                await mock.unwrap(system.browse_access_log)(
                    self.limit, self.offset,
                    self.filter, self.sorter,
                )
