import exceptions
import log
from base.enum import RoleType

from .base import FetchOne


async def read_global_role_by_account_id(account_id: int) -> RoleType:
    async with FetchOne(
            event='get global role by account id',
            sql=r'SELECT role'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_account_id(class_id: int, account_id: int) -> RoleType:
    async with FetchOne(
            event='get class role by account id',
            sql=r'SELECT role'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s'
                r'   AND member_id = %(account_id)s',
            class_id=class_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def any_class_role(member_id: int, role: RoleType) -> bool:
    try:
        async with FetchOne(
                event='',
                sql=r'SELECT *'
                    r'  FROM class_member'
                    r' WHERE member_id = %(member_id)s'
                    r'   AND role_type = %(role)s',
                member_id=member_id,
                role=role,
        ):
            pass
    except exceptions.persistence.NotFound:
        return False
    else:
        return True


async def read_team_role_by_account_id(team_id: int, account_id: int) -> RoleType:
    async with FetchOne(
            event='get team role by account id',
            sql=r'SELECT role'
                r'  FROM team_member'
                r' WHERE team_id = %(team_id)s'
                r'   AND member_id = %(account_id)s',
            team_id=team_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)
