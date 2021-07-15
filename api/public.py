from typing import Optional

from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from base.enum import RoleType
from config import config, app_config
import exceptions as exc
from middleware import APIRouter, JSONResponse, enveloped
import persistence.database as db
import persistence.email as email
from util import security, validator
import asyncpg


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
class AddAccountInput(BaseModel):
    # Account
    name: str
    password: str
    nickname: str
    real_name: str
    alternative_email: Optional[str] = ...
    # Student card
    institute_id: int
    department: str
    student_id: str
    institute_email_prefix: str


@router.post('/account', tags=['Account'], response_class=JSONResponse)
@enveloped
async def add_account(data: AddAccountInput) -> None:
    # 要先檢查以免創立了帳號後才出事
    try:
        institute = await db.institute.read(data.institute_id, include_disabled=False)
    except exc.NotFound:
        raise exc.InvalidInstitute

    if data.student_id != data.institute_email_prefix:
        raise exc.EmailNotMatch
    
    if data.alternative_email and not validator.is_valid_email(data.alternative_email):
            raise exc.InvalidEmail

    try:
        account_id = await db.account.add(name=data.name, pass_hash=security.hash_password(data.password),
                                          nickname=data.nickname, real_name=data.real_name, role=RoleType.guest)
    except asyncpg.exceptions.UniqueViolationError:
        raise exc.AccountExists

    institute_email = f"{data.institute_email_prefix}@{institute.email_domain}"
    code = await db.account.add_email_verification(email=institute_email, account_id=account_id,
                                                   institute_id=data.institute_id, department=data.department, student_id=data.student_id)
    await email.verification.send(to=institute_email, code=code)

    if data.alternative_email:
        # Alternative email 不直接寫進去，等 verify 的時候再寫進 db
        code = await db.account.add_email_verification(email=data.alternative_email, account_id=account_id)
        await email.verification.send(to=data.alternative_email, code=code)


# Warning: this location is statically used in email string
# Use "get" for convenience (access from browser)
@router.get('/email-verification', tags=['Account', 'Student Card'], response_class=HTMLResponse)
@router.post('/email-verification', tags=['Account', 'Student Card'], response_class=HTMLResponse)
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


@router.post('/account/jwt', tags=['Account'], response_class=JSONResponse)
@enveloped
async def login(data: LoginInput) -> str:
    try:
        account_id, pass_hash, is_4s_hash = await db.account.read_login_by_name(name=data.name)
    except exc.NotFound:
        raise exc.LoginFailed  # Not to let user know why login failed

    # Verify
    if is_4s_hash:
        if not security.verify_password_4s(to_test=data.password, hashed=pass_hash):
            raise exc.LoginFailed  # Not to let user know why login failed
        else:
            await db.account.edit_pass_hash(account_id=account_id, pass_hash=security.hash_password(data.password))
    else:
        if not security.verify_password(to_test=data.password, hashed=pass_hash):
            raise exc.LoginFailed  # Not to let user know why login failed

    # Get jwt
    login_token = security.encode_jwt(account_id=account_id, expire=config.login_expire)
    return login_token
