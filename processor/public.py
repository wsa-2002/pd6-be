from typing import Optional
from dataclasses import dataclass

from fastapi.responses import HTMLResponse
import pydantic
from pydantic import BaseModel

import exceptions as exc
from middleware import APIRouter, JSONResponse, enveloped
import service

from .util import model

router = APIRouter(tags=['Public'])


USERNAME_PROHIBITED_CHARS = r'`#$%&*\/?'


@router.get("/", status_code=418, response_class=HTMLResponse)
async def default_page():
    return await service.public.default_page()


class AddAccountInput(BaseModel):
    # Account
    username: str
    password: str
    nickname: str
    real_name: str
    alternative_email: Optional[pydantic.EmailStr] = model.can_omit
    # Student card
    institute_id: int
    student_id: str
    institute_email_prefix: str


@router.post('/account', tags=['Account'], response_class=JSONResponse)
@enveloped
async def add_account(data: AddAccountInput) -> None:
    # 要先檢查以免創立了帳號後才出事
    if any(char in data.username for char in USERNAME_PROHIBITED_CHARS):
        raise exc.account.IllegalCharacter

    try:
        institute = await service.institute.read(data.institute_id, include_disabled=False)
    except exc.persistence.NotFound:
        raise exc.account.InvalidInstitute

    if data.student_id != data.institute_email_prefix:
        raise exc.account.StudentIdNotMatchEmail

    if service.student_card.is_duplicate(institute.id, data.student_id):
        raise exc.account.StudentCardExists

    try:
        account_id = await service.account.add(username=data.username, password=data.password,
                                               nickname=data.nickname, real_name=data.real_name)
    except exc.persistence.UniqueViolationError:
        raise exc.account.UsernameExists

    institute_email = f"{data.institute_email_prefix}@{institute.email_domain}"
    await service.student_card.add(account_id=account_id, institute_email=institute_email,
                                   institute_id=institute.id, student_id=data.student_id)

    if data.alternative_email:
        await service.account.edit_alternative_email(account_id=account_id, alternative_email=data.alternative_email)


# Warning: this location is statically used in email string
# Use "get" for convenience (access from browser)
@router.get('/email-verification', tags=['Account', 'Student Card'], response_class=HTMLResponse)
@router.post('/email-verification', tags=['Account', 'Student Card'], response_class=HTMLResponse)
async def email_verification(code: str):
    try:
        await service.account.verify_email(code=code)
    except exc.persistence.NotFound:
        return 'Your verification code is not valid.'
    else:
        return 'Your email has been verified.'


class LoginInput(BaseModel):
    username: str
    password: str


@dataclass
class LoginOutput:
    token: str
    account_id: int


@router.post('/account/jwt', tags=['Account'], response_class=JSONResponse)
@enveloped
async def login(data: LoginInput) -> LoginOutput:
    login_token, account_id = await service.public.login(username=data.username, password=data.password)
    return LoginOutput(token=login_token, account_id=account_id)


class ForgetPasswordInput(BaseModel):
    email: str


@router.post('/account/forget-password', tags=['Account'], response_class=JSONResponse)
@enveloped
async def forget_password(data: ForgetPasswordInput) -> None:
    await service.public.forget_password(account_email=data.email)


class ResetPasswordInput(BaseModel):
    code: str
    password: str


@router.post('/account/reset-password', tags=['Account'], response_class=JSONResponse)
async def reset_password(data: ResetPasswordInput) -> None:
    await service.public.reset_password(code=data.code, password=data.password)
