from typing import Optional
from dataclasses import dataclass

import fastapi.routing
from pydantic import BaseModel

import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, JSONResponse, enveloped, Request
import service

from .util import rbac

router = APIRouter(route_class=fastapi.routing.APIRoute)  # Does not log the I/O data


class LoginInput(BaseModel):
    username: str
    password: str


@dataclass
class LoginOutput:
    token: str
    account_id: int


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
