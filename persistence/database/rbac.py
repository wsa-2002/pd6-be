from base.enum import RoleType

from .base import SafeExecutor


async def get_global_role_by_account_id(account_id: int) -> RoleType:
    async with SafeExecutor(
            event='get global role by account id',
            sql=r'SELECT account.role'
                r'  FROM account'
                r' WHERE account.id = %(account_id)s',
            account_id=account_id,
            fetch=1,
    ) as (role,):
        return RoleType(role)


async def get_class_role_by_account_id(class_id: int, account_id: int) -> RoleType:
    async with SafeExecutor(
            event='get class role by account id',
            sql=r'SELECT class_member.role'
                r'  FROM class_member'
                r' WHERE class_member.class_id = %(class_id)s'
                r'   AND class_member.member_id = %(account_id)s',
            class_id=class_id,
            account_id=account_id,
            fetch=1,
    ) as (role,):
        return RoleType(role)


async def get_team_role_by_account_id(team_id: int, account_id: int) -> RoleType:
    async with SafeExecutor(
            event='get team role by account id',
            sql=r'SELECT team_member.role'
                r'  FROM team_member'
                r' WHERE team_member.team_id = %(class_id)s'
                r'   AND team_member.member_id = %(account_id)s',
            team_id=team_id,
            account_id=account_id,
            fetch=1,
    ) as (role,):
        return RoleType(role)
