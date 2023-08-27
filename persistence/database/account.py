from typing import Tuple, Sequence, Optional, Iterable
from uuid import UUID

from base import do
from base.enum import RoleType
import exceptions as exc

from . import student_card
from .base import AutoTxConnection, FetchOne, OnlyExecute, FetchAll, ParamDict
from .util import compile_values


async def add(username: str, pass_hash: str, nickname: str, real_name: str, role: RoleType) -> int:
    async with FetchOne(
            event='add account',
            sql=r'INSERT INTO account'
                r'            (username, pass_hash, nickname, real_name, role)'
                r'     VALUES (%(username)s, %(pass_hash)s, %(nickname)s, %(real_name)s, %(role)s)'
                r'  RETURNING id',
            username=username, pass_hash=pass_hash, nickname=nickname, real_name=real_name, role=role,
    ) as (account_id,):
        return account_id


async def batch_add_normal(accounts: Sequence[tuple[str, str, str, str, str]], role=RoleType.normal):
    values = [(real_name, username, pass_hash, alternative_email, nickname, role)
              for real_name, username, pass_hash, alternative_email, nickname in accounts]

    value_sql, value_params = compile_values(values)

    # account in accounts: Real name, username, pass_hash, alternative email, nickname
    async with OnlyExecute(
            event='batch add normal account',
            sql=fr'INSERT INTO account'
                fr'            (real_name, username, pass_hash, alternative_email, nickname, role)'
                fr'     VALUES {value_sql}',
            *value_params,
    ):
        return


async def add_normal(username: str, pass_hash: str, real_name: str, nickname: str,
                     alternative_email: str = None, role=RoleType.normal) -> int:
    async with FetchOne(
            event='add account',
            sql=r'INSERT INTO account'
                r'            (username, pass_hash, real_name, role, alternative_email, nickname)'
                r'     VALUES (%(username)s, %(pass_hash)s, %(real_name)s, %(role)s, %(alternative_email)s, %(nickname)s)'
                r'  RETURNING id',
            username=username, pass_hash=pass_hash, real_name=real_name,
            role=role, alternative_email=alternative_email, nickname=nickname,
    ) as (account_id,):
        return account_id


async def read(account_id: int, *, include_deleted: bool = False) -> do.Account:
    async with FetchOne(
            event='read account info',
            sql=fr'SELECT id, username, nickname, real_name, role, is_deleted, alternative_email'
                fr'  FROM account'
                fr' WHERE id = %(account_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            account_id=account_id,
    ) as (id_, username, nickname, real_name, role, is_deleted, alternative_email):
        return do.Account(id=id_, username=username, nickname=nickname, real_name=real_name, role=RoleType(role),
                          is_deleted=is_deleted, alternative_email=alternative_email)


async def edit(account_id: int, username: str = None, real_name: str = None, nickname: str = None) -> None:
    to_updates: ParamDict = {}

    if username is not None:
        to_updates['username'] = username
    if real_name is not None:
        to_updates['real_name'] = real_name
    if nickname is not None:
        to_updates['nickname'] = nickname

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='update account info',
            sql=fr'UPDATE account'
                fr'   SET {set_sql}'
                fr' WHERE id = %(account_id)s',
            account_id=account_id,
            **to_updates,
    ):
        return


async def delete(account_id: int) -> None:
    async with AutoTxConnection(event='soft delete account and HARD delete student card') as conn:
        await conn.execute(
            r'DELETE FROM student_card'
            r' WHERE account_id = $1',
            account_id,
        )

        await conn.execute(
            r'UPDATE account'
            r'   SET is_deleted = $1'
            r' WHERE id = $2',
            True, account_id,
        )


async def delete_alternative_email_by_id(account_id: int) -> None:
    async with OnlyExecute(
            event='set account delete alternative email',
            sql=r'UPDATE account'
                r'   SET alternative_email = %(alternative_email)s'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
            alternative_email=None,
    ):
        return


async def read_login_by_username(username: str, include_deleted: bool = False, case_sensitive: bool = False) \
        -> Tuple[int, str, bool]:
    async with FetchOne(
            event='read account login by username',
            sql=fr'SELECT id, pass_hash, is_4s_hash'
                fr'  FROM account'
                fr' WHERE {"username = %(username)s" if case_sensitive else "LOWER(username) = LOWER(%(username)s)"}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            username=username,
    ) as (id_, pass_hash, is_4s_hash):
        return id_, pass_hash, is_4s_hash


async def browse_by_email(email: str, username: str = None, search_exhaustive=False, case_sensitive: bool = False) \
        -> Sequence[do.Account]:
    username_eq = 'username = %(username)s' if case_sensitive else 'LOWER(username) = LOWER(%(username)s)'

    accounts = []

    # institute_email
    async with FetchAll(
            event='batch read account by institute_email',
            sql=fr'SELECT account.id, username, nickname, real_name, role, is_deleted, alternative_email'
                fr'  FROM account'
                fr' INNER JOIN student_card'
                fr'         ON student_card.account_id = account.id'
                fr'        AND LOWER(student_card.email) = LOWER(%(email)s)'
                fr' WHERE NOT is_deleted'
                fr' {"AND " + username_eq if username else ""}',
            email=email, username=username,
            raise_not_found=False,
    ) as results:
        accounts += [do.Account(id=id_, username=username, nickname=nickname, real_name=real_name, role=RoleType(role),
                                is_deleted=is_deleted, alternative_email=alternative_email)
                     for (id_, username, nickname, real_name, role, is_deleted, alternative_email) in results]

    if accounts and not search_exhaustive:
        return accounts

    # alternative_email
    async with FetchAll(
            event='batch read account by alternative_email',
            sql=fr'SELECT id, username, nickname, real_name, role, is_deleted, alternative_email'
                fr'  FROM account'
                fr' WHERE LOWER(alternative_email) = LOWER(%(email)s)'
                fr'   AND NOT is_deleted'
                fr' {"AND " + username_eq if username else ""}',
            email=email, username=username,
            raise_not_found=False,
    ) as results:
        accounts += [do.Account(id=id_, username=username, nickname=nickname, real_name=real_name, role=RoleType(role),
                                is_deleted=is_deleted, alternative_email=alternative_email)
                     for (id_, username, nickname, real_name, role, is_deleted, alternative_email) in results]

    if not accounts:
        raise exc.persistence.NotFound

    return accounts


async def read_pass_hash(account_id: int, include_4s_hash: bool = False) -> str:
    async with FetchOne(
            event='read pass hash',
            sql=fr'SELECT pass_hash'
                fr'  FROM account'
                fr' WHERE id = %(account_id)s'
                fr'{" AND NOT is_4s_hash" if not include_4s_hash else ""}',
            account_id=account_id,
    ) as (pass_hash,):
        return pass_hash


async def add_email_verification(email: str, account_id: int, institute_id: int = None,
                                 student_id: str = None) -> str:
    async with FetchOne(
            event='create email verification',
            sql=r'INSERT INTO email_verification'
                r'            (email, account_id, institute_id, student_id)'
                r'     VALUES (%(email)s, %(account_id)s, %(institute_id)s, %(student_id)s)'
                r'  RETURNING code',
            email=email,
            account_id=account_id,
            institute_id=institute_id,
            student_id=student_id,
    ) as (code,):
        return code


async def verify_email(code: UUID) -> None:
    async with AutoTxConnection(event='Verify email') as conn:
        try:
            email, account_id, institute_id, student_id = await conn.fetchrow(
                r'UPDATE email_verification'
                r'   SET is_consumed = $1'
                r' WHERE code = $2'
                r'   AND is_consumed = $3'
                r' RETURNING email, account_id, institute_id, student_id',
                True, code, False)
        except TypeError:
            raise exc.persistence.NotFound

        if student_id:  # student card email
            if await student_card.is_duplicate(institute_id, student_id):
                raise exc.account.StudentCardExists
            await conn.execute(r'UPDATE student_card'
                               r'   SET is_default = $1'
                               r' WHERE account_id = $2'
                               r'   AND is_default = $3',
                               False, account_id, True)
            await conn.execute(r'INSERT INTO student_card'
                               r'            (account_id, institute_id, student_id, email, is_default)'
                               r'     VALUES ($1, $2, $3, $4, $5)',
                               account_id, institute_id, student_id, email, True)
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


async def edit_pass_hash(account_id: int, pass_hash: str):
    async with OnlyExecute(
            event='change password hash',
            sql=r'UPDATE account'
                r'   SET pass_hash = %(pass_hash)s, is_4s_hash = %(is_4s_hash)s'
                r' WHERE id = %(account_id)s',
            pass_hash=pass_hash,
            is_4s_hash=False,
            account_id=account_id,
    ):
        pass


async def reset_password(code: str, password_hash: str) -> None:
    async with AutoTxConnection(event='reset password') as conn:
        try:
            email, account_id, institute_id, student_id = await conn.fetchrow(
                r'UPDATE email_verification'
                r'   SET is_consumed = $1'
                r' WHERE code = $2'
                r'   AND is_consumed = $3'
                r' RETURNING email, account_id, institute_id, student_id',
                True, code, False)
        except TypeError:
            raise exc.persistence.NotFound

        await conn.execute(r'UPDATE account'
                           r'   SET pass_hash = $1, is_4s_hash = $2'
                           r' WHERE id = $3',
                           password_hash, False, account_id)


async def edit_default_student_card(account_id: int, student_card_id: int) -> None:
    async with OnlyExecute(
            event='set default student_card for account',
            sql=r'UPDATE student_card'
                r'   SET is_default = CASE'
                r'                        WHEN id = %(student_card_id)s THEN true'
                r'                        ELSE false'
                r'                    END'
                r' WHERE account_id = %(account_id)s',
            account_id=account_id,
            student_card_id=student_card_id,
    ):
        return


async def account_referral_to_id(account_referral: str) -> int:
    async with FetchOne(
            event='account referral to id',
            sql="SELECT account_referral_to_id(%(account_referral)s)",
            account_referral=account_referral,
    ) as (account_id,):
        if not account_id:
            raise exc.persistence.NotFound
        return account_id


async def browse_referral_wth_ids(account_ids: Iterable[int]) -> Sequence[Optional[str]]:
    value_sql = ','.join(f'({account_id})' for account_id in account_ids)
    if not value_sql:
        return []
    async with FetchAll(
            event='browse account referral with ids',
            sql=fr'SELECT account_id_to_referral(account_id::INTEGER)'
                fr'  FROM (VALUES {value_sql}) account_ids(account_id)',
    ) as results:
        return [result for result, in results]
