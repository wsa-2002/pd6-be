from typing import Optional

from . import do
from .base import SafeExecutor


async def get_info(account_id: int) -> do.Account:
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
async def set_info(account_id: int,
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
