from typing import Optional
from dataclasses import dataclass

import pydantic
from fastapi import UploadFile, File
from pydantic import BaseModel, constr

from base import enum
from base.enum import RoleType
import const
import exceptions as exc
from config import config
from middleware import APIRouter, JSONResponse, enveloped, auth, routing
import persistence.database as db
import service
from persistence import email
from util import security, model
from util.context import context

router = APIRouter(
    route_class=routing.NoLogAPIRoute,  # Does not log the I/O data
    dependencies=auth.doc_dependencies,
)


class LoginInput(BaseModel):
    username: str
    password: str


@dataclass
class LoginOutput:
    token: str
    account_id: int


class AddAccountInput(BaseModel):
    # Account
    username: model.TrimmedNonEmptyStr
    password: model.NonEmptyStr
    nickname: str
    real_name: str
    alternative_email: Optional[model.CaseInsensitiveEmailStr] = model.can_omit
    # Student card
    institute_id: int
    student_id: constr(to_lower=True)
    institute_email_prefix: constr(to_lower=True)


@router.post('/account', tags=['Public', 'Account'], response_class=JSONResponse)
@enveloped
async def add_account(data: AddAccountInput) -> None:
    # 要先檢查以免創立了帳號後才出事
    if any(char in data.username for char in const.USERNAME_PROHIBITED_CHARS):
        raise exc.account.IllegalCharacter

    try:
        institute = await db.institute.read(data.institute_id, include_disabled=False)
    except exc.persistence.NotFound:
        raise exc.account.InvalidInstitute

    if data.student_id != data.institute_email_prefix:
        raise exc.account.StudentIdNotMatchEmail

    if await db.student_card.is_duplicate(institute.id, data.student_id):
        raise exc.account.StudentCardExists

    try:
        account_id = await db.account.add(username=data.username, pass_hash=security.hash_password(data.password),
                                          nickname=data.nickname, real_name=data.real_name, role=enum.RoleType.guest)
    except exc.persistence.UniqueViolationError:
        raise exc.account.UsernameExists

    institute_email = f"{data.institute_email_prefix}@{institute.email_domain}"
    try:
        institute_email = pydantic.parse_obj_as(model.CaseInsensitiveEmailStr, institute_email)
    except pydantic.EmailError as e:
        raise exc.account.InvalidEmail from e

    code = await db.account.add_email_verification(email=institute_email, account_id=account_id,
                                                   institute_id=data.institute_id, student_id=data.student_id)
    account = await db.account.read(account_id)
    await email.verification.send(to=institute_email, code=code, username=account.username)

    # 先 update email 因為如果失敗就整個失敗
    if data.alternative_email is ...:
        pass
    elif data.alternative_email:  # 加或改 alternative email
        code = await db.account.add_email_verification(email=data.alternative_email, account_id=account_id)
        account = await db.account.read(account_id)
        await email.verification.send(to=data.alternative_email, code=code, username=account.username)
    else:  # 刪掉 alternative email
        await db.account.delete_alternative_email_by_id(account_id=account_id)


@router.post('/account/jwt', tags=['Public', 'Account'], response_class=JSONResponse)
@enveloped
async def login(data: LoginInput) -> LoginOutput:
    try:
        account_id, pass_hash, is_4s_hash = await db.account.read_login_by_username(username=data.username)
    except exc.persistence.NotFound:
        raise exc.account.LoginFailed  # Not to let user know why login failed

    # Verify
    if is_4s_hash:
        if not security.verify_password_4s(to_test=data.password, hashed=pass_hash):
            raise exc.account.LoginFailed  # Not to let user know why login failed
        else:
            await db.account.edit_pass_hash(account_id=account_id, pass_hash=security.hash_password(data.password))
    else:
        if not security.verify_password(to_test=data.password, hashed=pass_hash):
            raise exc.account.LoginFailed  # Not to let user know why login failed

    # Get jwt
    login_token = security.encode_jwt(account_id=account_id, expire=config.login_expire, cached_username=data.username)

    return LoginOutput(token=login_token, account_id=account_id)


class AddNormalAccountInput(BaseModel):
    real_name: str
    username: model.TrimmedNonEmptyStr
    password: model.NonEmptyStr
    nickname: str = ''
    alternative_email: Optional[model.CaseInsensitiveEmailStr] = model.can_omit


@router.post('/account-normal', tags=['Account'], response_class=JSONResponse)
@enveloped
async def add_normal_account(data: AddNormalAccountInput) -> model.AddOutput:
    """
    ### 權限
    - System Manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    # 要先檢查以免創立了帳號後才出事
    if any(char in data.username for char in const.USERNAME_PROHIBITED_CHARS):
        raise exc.account.IllegalCharacter

    try:
        account_id = await db.account.add_normal(username=data.username,
                                                 pass_hash=security.hash_password(data.password),
                                                 real_name=data.real_name, nickname=data.nickname,
                                                 alternative_email=data.alternative_email
                                                 if data.alternative_email is not ... else None)
    except exc.persistence.UniqueViolationError:
        raise exc.account.UsernameExists

    return model.AddOutput(id=account_id)


@router.post('/account-import', tags=['Account'], response_class=JSONResponse)
@enveloped
async def import_account(account_file: UploadFile = File(...)):
    """
    ### 權限
    - System Manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    await service.csv.import_account(account_file=account_file.file)


class EditPasswordInput(BaseModel):
    old_password: Optional[str]
    new_password: model.NonEmptyStr


@router.put('/account/{account_id}/pass_hash', tags=['Account'], response_class=JSONResponse)
@enveloped
async def edit_password(account_id: int, data: EditPasswordInput):
    """
    ### 權限
    - System Manager
    - Self (need old password)
    """

    is_self = context.account.id == account_id
    if is_self:
        pass_hash = await db.account.read_pass_hash(account_id=account_id, include_4s_hash=False)
        if not security.verify_password(to_test=data.old_password, hashed=pass_hash):
            raise exc.account.PasswordVerificationFailed

        return await db.account.edit_pass_hash(account_id=account_id,
                                               pass_hash=security.hash_password(data.new_password))

    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    if is_manager:
        return await db.account.edit_pass_hash(account_id=account_id,
                                               pass_hash=security.hash_password(data.new_password))

    raise exc.NoPermission


class ResetPasswordInput(BaseModel):
    code: str
    password: model.NonEmptyStr


@router.post('/account/reset-password', tags=['Account'], response_class=JSONResponse)
@enveloped
async def reset_password(data: ResetPasswordInput) -> None:
    await db.account.reset_password(code=data.code, password_hash=security.hash_password(data.password))
