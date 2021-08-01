from typing import Tuple, Sequence

from base import do
from base.enum import RoleType
import exceptions as exc

from .base import SafeExecutor, SafeConnection


async def add(username: str, pass_hash: str, nickname: str, real_name: str, role: RoleType) -> int:
    async with SafeExecutor(
            event='add account',
            sql=r'INSERT INTO account'
                r'            (username, pass_hash, nickname, real_name, role)'
                r'     VALUES (%(username)s, %(pass_hash)s, %(nickname)s, %(real_name)s, %(role)s)'
                r'  RETURNING id',
            username=username, pass_hash=pass_hash, nickname=nickname, real_name=real_name, role=role,
            fetch=1,
    ) as (account_id,):
        return account_id


async def browse(include_deleted: bool = False) -> Sequence[do.BrowseAccountOutput]:
    async with SafeExecutor(
            event='browse account',
            sql=fr'SELECT account.id, student_card.student_id, account.real_name,'
                fr'       account.username, account.nickname, account.alternative_email'
                fr'  FROM account'
                fr'       INNER JOIN student_card'
                fr'               ON student_card.account_id = account.id'
                fr'{" WHERE NOT account.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY account.id ASC',
            fetch='all',
    ) as records:
        return [do.BrowseAccountOutput(id=id_, student_id=student_id, real_name=real_name, username=username,
                                       nickname=nickname, alternative_email=alternative_email)
                for (id_, student_id, real_name, username, nickname, alternative_email)
                in records]


async def read(account_id: int, *, include_deleted: bool = False) -> do.Account:
    async with SafeExecutor(
            event='read account info',
            sql=fr'SELECT id, username, nickname, real_name, role, is_deleted, alternative_email'
                fr'  FROM account'
                fr' WHERE id = %(account_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            account_id=account_id,
            fetch=1,
    ) as (id_, username, nickname, real_name, role, is_deleted, alternative_email):
        return do.Account(id=id_, username=username, nickname=nickname, real_name=real_name, role=RoleType(role),
                          is_deleted=is_deleted, alternative_email=alternative_email)


# Uses ellipsis (...) as default value for values that can be set to None
async def edit(account_id: int,
               nickname: str = ...) -> None:
    to_updates = {}
    if nickname is not ...:
        to_updates['nickname'] = nickname

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update account info',
            sql=fr'UPDATE account'
                fr'   SET {set_sql}'
                fr' WHERE id = %(account_id)s',
            account_id=account_id,
            **to_updates,
    ):
        return


async def delete(account_id: int) -> None:
    async with SafeExecutor(
            event='soft delete account',
            sql=fr'UPDATE account'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(account_id)s',
            account_id=account_id,
            is_deleted=True,
    ):
        return


async def delete_alternative_email_by_id(account_id: int) -> None:
    async with SafeExecutor(
            event='set account delete alternative email',
            sql=fr'UPDATE account'
                fr'   SET alternative_email = %(alternative_email)s'
                fr' WHERE id = %(account_id)s',
            account_id=account_id,
            alternative_email=None,
    ):
        return


async def read_login_by_username(username: str, include_deleted: bool = False) -> Tuple[int, str, bool]:
    async with SafeExecutor(
            event='read account login by username',
            sql=fr'SELECT id, pass_hash, is_4s_hash'
                fr'  FROM account'
                fr' WHERE username = %(username)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            username=username,
            fetch=1,
    ) as (id_, pass_hash, is_4s_hash):
        return id_, pass_hash, is_4s_hash


async def read_id_by_email(email: str) -> int:
    try:  # institute_email
        async with SafeExecutor(
                event='read account by institute_email',
                sql=fr'SELECT account_id'
                    fr'  FROM student_card'
                    fr' WHERE email = %(email)s',
                email=email,
                fetch=1,
        ) as (id_,):
            return id_

    except exc.persistence.NotFound:  # alternative_email
        async with SafeExecutor(
                event='read account by alternative_email',
                sql=fr'SELECT id'
                    fr'  FROM account'
                    fr' WHERE alternative_email = %(email)s'
                    fr' AND NOT is_deleted',
                email=email,
                fetch=1,
        ) as (id_,):
            return id_


async def read_pass_hash(account_id: int, include_4s_hash: bool = False) -> str:
    async with SafeExecutor(
            event='read pass hash',
            sql=fr'SELECT pass_hash'
                fr'  FROM account'
                fr' WHERE id = %(account_id)s'
                fr'{" AND NOT is_4s_hash" if not include_4s_hash else ""}',
            account_id=account_id,
            fetch=1,
    ) as (pass_hash,):
        return pass_hash


async def add_email_verification(email: str, account_id: int, institute_id: int = None, department: str = None,
                                 student_id: str = None) -> str:
    async with SafeExecutor(
            event='create email verification',
            sql=r'INSERT INTO email_verification'
                r'            (email, account_id, institute_id, department, student_id)'
                r'     VALUES (%(email)s, %(account_id)s, %(institute_id)s, %(department)s, %(student_id)s)'
                r'  RETURNING code',
            email=email,
            account_id=account_id,
            institute_id=institute_id,
            department=department,
            student_id=student_id,
            fetch=1,
    ) as (code,):
        return code


async def verify_email(code: str) -> None:
    async with SafeConnection(event='Verify email') as conn:
        async with conn.transaction():
            try:
                email, account_id, institute_id, department, student_id = await conn.fetchrow(
                    r'UPDATE email_verification'
                    r'   SET is_consumed = $1'
                    r' WHERE code = $2'
                    r'   AND is_consumed = $3'
                    r' RETURNING email, account_id, institute_id, department, student_id',
                    True, code, False)
            except TypeError:
                raise exc.persistence.NotFound

            if student_id:  # student card email
                await conn.execute(r'UPDATE student_card'
                                   r'   SET is_default = $1'
                                   r' WHERE account_id = $2'
                                   r'   AND is_default = $3',
                                   False, account_id, True)
                await conn.execute(r'INSERT INTO student_card'
                                   r'            (account_id, institute_id, department, student_id, email, is_default)'
                                   r'     VALUES ($1, $2, $3, $4, $5, $6)',
                                   account_id, institute_id, department, student_id, email, True)
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
    async with SafeExecutor(
            event='change password hash',
            sql=fr'UPDATE account'
                fr'   SET pass_hash = %(pass_hash)s, is_4s_hash = %(is_4s_hash)s'
                fr' WHERE id = %(account_id)s',
            pass_hash=pass_hash,
            is_4s_hash=False,
            account_id=account_id,
    ):
        pass


async def reset_password(code: str, password_hash: str) -> None:
    async with SafeConnection(event='reset password') as conn:
        async with conn.transaction():
            try:
                email, account_id, institute_id, department, student_id = await conn.fetchrow(
                    r'UPDATE email_verification'
                    r'   SET is_consumed = $1'
                    r' WHERE code = $2'
                    r'   AND is_consumed = $3'
                    r' RETURNING email, account_id, institute_id, department, student_id',
                    True, code, False)
            except TypeError:
                raise exc.persistence.NotFound

            await conn.execute(r'UPDATE account'
                               r'   SET pass_hash = $1, is_4s_hash = $2'
                               r' WHERE id = $3',
                               password_hash, False, account_id)


async def edit_default_student_card(account_id: int, student_card_id: int) -> None:
    async with SafeExecutor(
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
