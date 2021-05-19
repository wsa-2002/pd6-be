from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from base.deco import validated_dataclass
from base.enum import RoleType
from config import config, app_config
import exceptions as exc
from middleware import envelope
import persistence.database as db
from util import email, security


router = APIRouter(tags=['Public'])


@router.get("/", status_code=418, response_class=HTMLResponse)
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


# @validated_dataclass
class CreateAccountInput(BaseModel):
    # Account
    name: str
    password: str
    nickname: str
    real_name: str
    alternative_email: Optional[str]
    # Student card
    institute_id: int
    department: str
    student_id: str
    institute_email: str


@router.post('/account', tags=['Account-Control'], response_class=envelope.JSONResponse)
async def create_account(data: CreateAccountInput) -> None:
    account_id = await db.account.add(name=data.name, pass_hash=security.hash_password(data.password),
                                      nickname=data.nickname, real_name=data.real_name, role=RoleType.guest,
                                      is_enabled=True)
    student_card_id = await db.student_card.add(
        account_id=account_id,
        institute_id=data.institute_id,
        department=data.department,
        student_id=data.student_id,
        email=data.institute_email,
        is_enabled=False,  # Not yet verified => disabled
    )

    code = await db.account.add_email_verification(email=data.institute_email,
                                                   account_id=account_id, student_card_id=student_card_id)
    await email.send_email_verification_email(to=data.institute_email, code=code)

    if data.alternative_email:
        # Alternative email 不直接寫進去，等 verify 的時候再寫進 db
        code = await db.account.add_email_verification(email=data.alternative_email, account_id=account_id)
        await email.send_email_verification_email(to=data.alternative_email, code=code)


# Warning: this location is statically used in email string
# Use "get" for convenience (access from browser)
@router.get('/email-verification', tags=['Account-Control'], response_class=HTMLResponse)
@router.post('/email-verification', tags=['Account-Control'], response_class=HTMLResponse)
async def email_verification(code: str):
    try:
        await db.account.verify_email(code=code)
    except exc.NotFound:
        return 'Your verification code is not valid.'
    else:
        return 'Your email has been verified.'


# @validated_dataclass
class LoginInput(BaseModel):
    name: str
    password: str


@router.post('/account/jwt', tags=['Account-Control'], response_class=envelope.JSONResponse)
async def login(data: LoginInput) -> str:
    try:
        account_id, pass_hash = await db.account.get_login_by_name(name=data.name)
    except exc.NotFound:
        raise exc.LoginFailed  # Not to let user know why login failed

    # Verify
    if not security.verify_password(to_test=data.password, hashed=pass_hash):
        raise exc.LoginFailed

    # Get jwt
    login_token = security.encode_jwt(account_id=account_id, expire=config.login_expire)
    return login_token
