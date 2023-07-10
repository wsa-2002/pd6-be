import unittest
from unittest.mock import patch, AsyncMock

from base import enum, do
import exceptions as exc  # noqa
from service import rbac


class TestValidateInherit(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.team = do.Team(
            id=1,
            name='team',
            class_id=1,
            label='label',
            is_deleted=False
        )

    async def test_validate_inherit_team_id_team_normal(self):
        @patch('persistence.database.rbac.read_team_role_by_account_id',
               AsyncMock(return_value=enum.RoleType.normal))
        async def test():
            return await rbac.validate_inherit(account_id=1, min_role=enum.RoleType.normal, team_id=1)

        res = await test()
        self.assertTrue(res)

    async def test_validate_inherit_team_id_class_normal(self):
        with patch('persistence.database.rbac') as db_rbac:
            with patch('persistence.database.team') as team:
                db_rbac.read_team_role_by_account_id = AsyncMock(side_effect=exc.persistence.NotFound)
                team.read = AsyncMock(return_value=self.team)
                db_rbac.read_class_role_by_account_id = AsyncMock(return_value=enum.RoleType.normal)
                data = await rbac.validate_inherit(account_id=1, min_role=enum.RoleType.normal, team_id=1)

                team.read.assert_called_once()
                db_rbac.read_class_role_by_account_id.assert_called_once()
                self.assertTrue(data)
