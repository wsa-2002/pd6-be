from typing import Tuple

from config import config, app_config
import exceptions as exc
import persistence.database as db
import persistence.email as email
from util import security


async def default_page():
    doc_paths = []
    if _url := app_config.docs_url:
        doc_paths.append(f'<a href="{_url}">{_url}</a>')
    if _url := app_config.redoc_url:
        doc_paths.append(f'<a href="{_url}">{_url}</a>')
    return fr"""
{' or '.join(doc_paths)}
<br>
<br>
<img src="https://i.imgur.com/dBUZ3Ig.png" alt="I am not PDOGS" height="90%">
"""


async def login(username: str, password: str) -> Tuple[str, int]:
    """
    :return: jwt and account id
    """
    try:
        account_id, pass_hash, is_4s_hash = await db.account.read_login_by_username(username=username)
    except exc.persistence.NotFound:
        raise exc.account.LoginFailed  # Not to let user know why login failed

    # Verify
    if is_4s_hash:
        if not security.verify_password_4s(to_test=password, hashed=pass_hash):
            raise exc.account.LoginFailed  # Not to let user know why login failed
        else:
            await db.account.edit_pass_hash(account_id=account_id, pass_hash=security.hash_password(password))
    else:
        if not security.verify_password(to_test=password, hashed=pass_hash):
            raise exc.account.LoginFailed  # Not to let user know why login failed

    # Get jwt
    login_token = security.encode_jwt(account_id=account_id, expire=config.login_expire)

    return login_token, account_id


async def forget_password(account_email: str) -> None:
    account_id = await db.account.read_id_by_email(account_email)

    code = await db.account.add_email_verification(email=account_email, account_id=account_id)
    await email.forget_password.send(to=account_email, code=code)


async def reset_password(code: str, password: str) -> None:
    await db.account.reset_password(code=code, password_hash=security.hash_password(password))
