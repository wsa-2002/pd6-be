from typing import Optional, Tuple

import exceptions
from base import do
from base.enum import RoleType

from .base import SafeExecutor, SafeConnection


async def add(name: str, pass_hash: str, nickname: str, real_name: str, role: RoleType, is_enabled: bool) -> int:
    async with SafeExecutor(
            event='add account',
            sql=r'INSERT INTO account'
                r'            (name, pass_hash, nickname, real_name, role, is_enabled)'
                r'     VALUES (%(name)s, %(pass_hash)s, %(nickname)s, %(real_name)s, %(role)s, %(is_enabled)s)'
                r'  RETURNING id',
            name=name, pass_hash=pass_hash, nickname=nickname, real_name=real_name, role=role, is_enabled=is_enabled,
            fetch=1,
    ) as (account_id,):
        return account_id


async def read(account_id: int) -> do.Account:
    async with SafeExecutor(
            event='read account info',
            sql=r'SELECT id, name, nickname, real_name, role_id, is_enabled, alternative_email'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
            fetch=1,
    ) as (id_, name, nickname, real_name, role_id, is_enabled, is_hidden, alternative_email):
        return do.Account(id=id_, name=name, nickname=nickname, real_name=real_name, role=role_id,
                          is_enabled=is_enabled, alternative_email=alternative_email)


# Uses ellipsis (...) as default value for values that can be set to None
async def edit(account_id: int,
               nickname: Optional[str] = ...):
    to_updates = {}
    if nickname is not ...:
        to_updates['nickname'] = nickname

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update account info',
            sql=fr'UPDATE account'
                fr' WHERE account.id = %(account_id)s'
                fr'   SET {set_sql}',
            account_id=account_id,
            **to_updates,
    ):
        return


async def delete_alternative_email_by_id(account_id: int):
    async with SafeExecutor(
            event='set account delete alternative email',
            sql=fr'UPDATE account'
                fr' WHERE account.id = %(account_id)s'
                fr'   SET alternative_email = %(alternative_email)s',
            account_id=account_id,
            alternative_email=None,
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


async def read_login_by_name(name: str, is_enabled: bool = True) -> Tuple[int, str]:
    async with SafeExecutor(
            event='read account login by name',
            sql=r'SELECT id, pass_hash'
                r'  FROM account'
                r' WHERE name = %(name)s'
                r'   AND is_enabled = %(is_enabled)s',
            name=name,
            is_enabled=is_enabled,
            fetch=1,
    ) as (id_, pass_hash):
        return id_, pass_hash


async def add_email_verification(email: str, account_id: int, student_card_id: int = None) -> str:
    async with SafeExecutor(
            event='create email verification',
            sql=r'INSERT INTO email_verification'
                r'            (email, account_id, student_card_id)'
                r'     VALUES (%(email)s, %(account_id)s, %(student_card_id)s)'
                r'  RETURNING code',
            email=email,
            account_id=account_id,
            student_card_id=student_card_id,
            fetch=1,
    ) as (code,):
        return code


async def verify_email(code: str):
    async with SafeConnection(event='Verify email') as conn:
        async with conn.transaction():
            try:
                email, account_id, student_card_id = await conn.fetchrow(
                    r'UPDATE email_verification'
                    r'   SET is_consumed = $1'
                    r' WHERE code = $2'
                    r'   AND is_consumed = $3'
                    r' RETURNING email, account_id, student_card_id',
                    True, code, False)
            except TypeError:
                raise exceptions.NotFound

            if student_card_id:  # student card email
                await conn.execute(r'UPDATE student_card'
                                   r'   SET is_enabled = $1'
                                   r' WHERE id = $2',
                                   True, student_card_id)
                await conn.execute(r'UPDATE account'
                                   r'   SET is_enabled = $1'
                                   r' WHERE id = $2',
                                   True, account_id)
                await conn.execute(r'UPDATE account'
                                   r'   SET role = $1'
                                   r' WHERE id = $2'
                                   r'   AND role = $3',
                                   RoleType.normal, account_id, RoleType.guest)
            else:  # alternative email
                await conn.execute(r'UPDATE account'
                                   r'   SET alternative_email = $1'
                                   r' WHERE id = $2',
                                   email, account_id)
