from dataclasses import dataclass
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from base.deco import validated_dataclass
from base.enum import RoleType
from config import config
import exceptions as exc
from middleware import envelope
import persistence.database as db
from util import security


router = APIRouter(tags=['Public'])


@router.get("/", status_code=418, response_class=HTMLResponse)
async def default_page():
    return r"""
<a href="/docs">/docs</a> or <a href="/redoc">/redoc</a>
<br>
<br>
<img src="https://i.imgur.com/dBUZ3Ig.png" alt="I am not PDOGS">
"""


@validated_dataclass
class CreateAccountInput:
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
                                      alternative_email=data.alternative_email, is_enabled=True)
    await db.student_card.add(
        account_id=account_id,
        institute_id=data.institute_id,
        department=data.department,
        student_id=data.student_id,
        email=data.institute_email,
        is_enabled=False,  # Not yet verified => disabled
    )

    # TODO: email validation


@validated_dataclass
class LoginInput:
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
