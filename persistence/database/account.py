from typing import Optional, Tuple

from base.enum import RoleType

from . import do
from .base import SafeExecutor


async def add(name: str, pass_hash: str, nickname: str, real_name: str, role: RoleType,
              alternative_email: Optional[str], is_enabled: bool) -> int:
    async with SafeExecutor(
            event='add account',
            sql=r'INSERT INTO account'
                r'            (name, pass_hash, nickname, real_name, role, alternative_email, is_enabled)'
                r'     VALUES (%(name)s, %(pass_hash)s, %(nickname)s, %(real_name)s, %(role)s, %(alternative_email)s,'
                r'             %(is_enabled)s)'
                r'  RETURNING id',
            name=name, pass_hash=pass_hash, nickname=nickname, real_name=real_name, role=role,
            alternative_email=alternative_email, is_enabled=is_enabled,
            fetch=1,
    ) as (account_id):
        return account_id


async def get_by_id(account_id: int) -> do.Account:
    async with SafeExecutor(
            event='get account info',
            sql=r'SELECT id, name, nickname, real_name, role_id, is_enabled, alternative_email'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
            fetch=1,
    ) as (id_, name, nickname, real_name, role_id, is_enabled, is_hidden, alternative_email):
        return do.Account(id=id_, name=name, nickname=nickname, real_name=real_name, role=role_id,
                          is_enabled=is_enabled, alternative_email=alternative_email)


# Uses ellipsis (...) as default value for values that can be set to None
async def set_by_id(account_id: int,
                    nickname: Optional[str] = ...):
    to_updates = {}
    if nickname is not ...:
        to_updates['nickname'] = nickname

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='set account info',
            sql=fr'UPDATE account'
                fr' WHERE account.id = %(account_id)s'
                fr'   SET {set_sql}',
            account_id=account_id,
            **to_updates,
    ):
        return


async def check_is_enabled(account_id: int) -> bool:
    async with SafeExecutor(
            event='check account enabled',
            sql=r'SELECT is_enabled'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
            fetch=1,
    ) as (is_enabled,):
        return is_enabled


async def set_enabled(account_id: int, is_enabled: bool):
    async with SafeExecutor(
            event='set account disabled',
            sql=fr'UPDATE account'
                fr' WHERE account.id = %(account_id)s'
                fr'   SET account.is_enabled = %(is_enabled)s',
            account_id=account_id,
            is_enabled=is_enabled,
    ):
        return


async def get_login_by_name(name: str, is_enabled: bool = True) -> Tuple[int, str]:
    async with SafeExecutor(
            event='get account login by name',
            sql=r'SELECT id, pass_hash'
                r'  FROM account'
                r' WHERE name = %(name)s'
                r'   AND is_enabled = %(is_enabled)s',
            name=name,
            is_enabled=is_enabled,
            fetch=1,
    ) as (id_, pass_hash):
        return id_, pass_hash
