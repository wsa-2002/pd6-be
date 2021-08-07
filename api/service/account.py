from base import enum
import exceptions as exc
import persistence.database as db
import persistence.email as email
import security


async def add(username: str, password: str, nickname: str, real_name: str, role=enum.RoleType.guest):
    return await db.account.add(username=username, pass_hash=security.hash_password(password),
                                nickname=nickname, real_name=real_name, role=role)


browse_account_with_default_student_id = db.account_vo.browse_account_with_default_student_id
read = db.account.read

edit_general = db.account.edit
edit_default_student_card = db.account.edit_default_student_card


async def edit_alternative_email(account_id: int, alternative_email: str = None) -> None:
    # 先 update email 因為如果失敗就整個失敗
    if alternative_email:  # 加或改 alternative email
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


verify_email = db.account.verify_email
delete = db.account.delete
