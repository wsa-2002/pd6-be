import unittest

from base import enum, do
import exceptions as exc
from util.test_tool import AsyncMockController

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
        with AsyncMockController() as controller:

            db_rbac = controller.mock_module('persistence.database.rbac')
            team = controller.mock_module('persistence.database.team')

            db_rbac.function('read_team_role_by_account_id').expect_call(
                team_id=1, account_id=1,
            ).raises(exc.persistence.NotFound)
            team.function('read').expect_call(team_id=1).returns(self.team)
            db_rbac.function('read_class_role_by_account_id').expect_call(
                class_id=1, account_id=1,
            ).returns(enum.RoleType.normal)

            data = await rbac.validate_inherit(account_id=1, min_role=enum.RoleType.normal, team_id=1)

            self.assertTrue(data)
