from typing import Optional
from dataclasses import dataclass

import fastapi.routing
import pydantic
from pydantic import BaseModel

from base.enum import RoleType
import const
import exceptions as exc
from middleware import APIRouter, JSONResponse, enveloped, Request
import service

from .util import model, rbac

router = APIRouter(route_class=fastapi.routing.APIRoute)  # Does not log the I/O data


class LoginInput(BaseModel):
    username: str
    password: str


@dataclass
class LoginOutput:
    token: str
    account_id: int


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


@router.post('/account', tags=['Public', 'Account'], response_class=JSONResponse)
@enveloped
async def add_account(data: AddAccountInput) -> None:
    # 要先檢查以免創立了帳號後才出事
    if any(char in data.username for char in const.USERNAME_PROHIBITED_CHARS):
        raise exc.account.IllegalCharacter

    try:
        institute = await service.institute.read(data.institute_id, include_disabled=False)
    except exc.persistence.NotFound:
        raise exc.account.InvalidInstitute

    if data.student_id != data.institute_email_prefix:
        raise exc.account.StudentIdNotMatchEmail

    if await service.student_card.is_duplicate(institute.id, data.student_id):
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


@router.post('/account/jwt', tags=['Public', 'Account'], response_class=JSONResponse)
@enveloped
async def login(data: LoginInput) -> LoginOutput:
    login_token, account_id = await service.public.login(username=data.username, password=data.password)
    return LoginOutput(token=login_token, account_id=account_id)


class EditPasswordInput(BaseModel):
    old_password: Optional[str]
    new_password: str


@router.put('/account/{account_id}/pass_hash', tags=['Account'], response_class=JSONResponse)
@enveloped
async def edit_password(account_id: int, data: EditPasswordInput, request: Request):
    """
    ### 權限
    - System Manager
    - Self (need old password)
    """

    is_self = request.account.id is account_id
    if is_self:
        return await service.account.edit_password(account_id=account_id,
                                                   old_password=data.old_password, new_password=data.new_password)

    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    if is_manager:
        return await service.account.force_edit_password(account_id=account_id, new_password=data.new_password)

    raise exc.NoPermission
