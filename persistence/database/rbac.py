import log
from base.enum import RoleType

from .base import SafeExecutor


@log.timed
async def read_global_role_by_account_id(account_id: int) -> RoleType:
    async with SafeExecutor(
            event='get global role by account id',
            sql=r'SELECT role'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
            fetch=1,
    ) as (role,):
        return RoleType(role)


@log.timed
async def read_class_role_by_account_id(class_id: int, account_id: int) -> RoleType:
    async with SafeExecutor(
            event='get class role by account id',
            sql=r'SELECT role'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s'
                r'   AND member_id = %(account_id)s',
            class_id=class_id,
            account_id=account_id,
            fetch=1,
    ) as (role,):
        return RoleType(role)


@log.timed
async def read_team_role_by_account_id(team_id: int, account_id: int) -> RoleType:
    async with SafeExecutor(
            event='get team role by account id',
            sql=r'SELECT role'
                r'  FROM team_member'
                r' WHERE team_id = %(class_id)s'
                r'   AND member_id = %(account_id)s',
            team_id=team_id,
            account_id=account_id,
            fetch=1,
    ) as (role,):
        return RoleType(role)
