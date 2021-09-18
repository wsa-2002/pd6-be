import csv
import codecs
import io
from typing import Tuple
import typing

from base import enum, do
import exceptions as exc
import persistence.database as db
import persistence.email as email
import persistence.s3 as s3
from util import security


ACCOUNT_TEMPLATE = b'RealName,Username,Password,AlternativeEmail,Nickname'
ACCOUNT_TEMPLATE_FILENAME = 'account_template.csv'


async def add(username: str, password: str, nickname: str, real_name: str, role=enum.RoleType.guest):
    return await db.account.add(username=username, pass_hash=security.hash_password(password),
                                nickname=nickname, real_name=real_name, role=role)


async def add_normal(username: str, password: str, real_name: str, alternative_email: str):
    return await db.account.add_normal(username=username, pass_hash=security.hash_password(password),
                                       real_name=real_name, alternative_email=alternative_email)


async def import_account(account_file: typing.IO):
    try:
        rows = csv.DictReader(codecs.iterdecode(account_file, 'utf_8_sig'))
        for row in rows:
            await db.account.add_normal(real_name=row['RealName'], username=row['Username'],
                                        pass_hash=security.hash_password(row['Password']),
                                        alternative_email=row['AlternativeEmail'], nickname=row['Nickname'])
    except UnicodeDecodeError:
        raise exc.FileDecodeError
    except:
        raise exc.IllegalInput


async def get_template_file() -> Tuple[do.S3File, str]:
    """
    :return: do.S3File and filename
    """
    with io.BytesIO(ACCOUNT_TEMPLATE) as file:
        s3_file = await s3.temp.upload(file=file)
        return s3_file, ACCOUNT_TEMPLATE_FILENAME


browse_with_default_student_card = db.account_vo.browse_with_default_student_card
browse_list_with_default_student_card = db.account_vo.browse_list_with_default_student_card
browse_with_class_role = db.class_.browse_role_by_account_id

read = db.account.read
read_with_default_student_card = db.account_vo.read_with_default_student_card

edit_general = db.account.edit
edit_default_student_card = db.account.edit_default_student_card

referral_to_id = db.account.account_referral_to_id


async def edit_alternative_email(account_id: int, alternative_email: str = None) -> None:
    # 先 update email 因為如果失敗就整個失敗
    if alternative_email is ...:
        return
    if alternative_email:  # 加或改 alternative email
        code = await db.account.add_email_verification(email=alternative_email, account_id=account_id)
        account = await db.account.read(account_id)
        await email.verification.send(to=alternative_email, code=code, username=account.username)
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
