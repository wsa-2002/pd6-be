from typing import Sequence

from base import do, vo
import exceptions as exc
import persistence.database as db
import persistence.email as email
from util import security, validator


async def browse_with_default_student_id() -> Sequence[vo.AccountWithDefaultStudentId]:
    return await db.account_vo.browse_account_with_default_student_id()


async def read(account_id: int) -> do.Account:
    return await db.account.read(account_id)


async def edit_general(account_id: int, nickname: str = None, real_name: str = None):
    await db.account.edit(account_id=account_id, nickname=nickname, real_name=real_name)


async def edit_alternative_email(account_id: int, alternative_email: str = None) -> None:
    # 先 update email 因為如果失敗就整個失敗
    if alternative_email:  # 加或改 alternative email
        if not validator.is_valid_email(alternative_email):
            raise exc.account.InvalidEmail
        code = await db.account.add_email_verification(email=alternative_email, account_id=account_id)
        await email.verification.send(to=alternative_email, code=code)
    else:  # 刪掉 alternative email
        await db.account.delete_alternative_email_by_id(account_id=account_id)


async def edit_password(account_id: int, old_password: str, new_password: str):
    pass_hash = await db.account.read_pass_hash(account_id=account_id, include_4s_hash=False)
    if not security.verify_password(to_test=old_password, hashed=pass_hash):
        raise exc.account.PasswordVerificationFailed

    await db.account.edit_pass_hash(account_id=account_id, pass_hash=security.hash_password(new_password))


async def force_edit_password(account_id: int, new_password: str):
    await db.account.edit_pass_hash(account_id=account_id, pass_hash=security.hash_password(new_password))


async def delete(account_id: int) -> None:
    await db.account.delete(account_id)


async def edit_default_student_card(account_id: int, student_card_id: int) -> None:
    await db.account.edit_default_student_card(
        account_id=account_id,
        student_card_id=student_card_id,
    )
