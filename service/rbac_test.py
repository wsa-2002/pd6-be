import unittest

from base import enum, do
import exceptions as exc
from util import mock

from . import rbac


class TestValidateInherit(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.team = do.Team(
            id=1,
            name='team',
            class_id=1,
            label='label',
            is_deleted=False
        )

    async def test_validate_inherit_team_id_class_normal_v2(self):
        with mock.Controller() as controller:

            db_rbac = controller.mock_module('persistence.database.rbac')
            team = controller.mock_module('persistence.database.team')

            db_rbac.async_func('read_team_role_by_account_id').call_with(
                team_id=1, account_id=1,
            ).raises(exc.persistence.NotFound)
            team.async_func('read').call_with(team_id=1).returns(self.team)
            db_rbac.async_func('read_class_role_by_account_id').call_with(
                class_id=1, account_id=1,
            ).returns(enum.RoleType.normal)

            data = await rbac.validate_inherit(account_id=1, min_role=enum.RoleType.normal, team_id=1)

            self.assertTrue(data)
