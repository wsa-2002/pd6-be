from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, envelope, auth
import persistence.database as db
import persistence.email as email
from util import rbac

router = APIRouter(
    tags=['Account'],
    default_response_class=envelope.JSONResponse,
)


@dataclass
class ReadAccountOutput:
    id: int
    name: str
    nickname: str
    role: str
    real_name: str
    alternative_email: Optional[str]


@router.get('/account/{account_id}')
async def read_account(account_id: int, request: auth.Request) -> ReadAccountOutput:
    """
    ### 權限
    - System Manager
    - Self
    - System Normal (個資除外)
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_normal = await rbac.validate(request.account.id, RoleType.normal)
    is_self = request.account.id is account_id

    if not (is_manager or is_normal or is_self):
        raise exc.NoPermission

    view_personal = is_self or is_manager

    target_account = await db.account.read(account_id)
    result = ReadAccountOutput(
        id=target_account.id,
        name=target_account.name,
        nickname=target_account.nickname,
        role=target_account.role,
        real_name=target_account.real_name if view_personal else None,
        alternative_email=target_account.alternative_email if view_personal else None,
    )

    return result


class EditAccountInput(BaseModel):
    nickname: str = None
    alternative_email: str = None


@router.patch('/account/{account_id}')
async def edit_account(account_id: int, data: EditAccountInput, request: auth.Request) -> None:
    """
    ### 權限
    - System Manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    # 不檢查 if data.nickname，因為 nickname 可以被刪掉 (設成 None)
    await db.account.edit(account_id=account_id, nickname=data.nickname)

    if data.alternative_email:  # 加或改 alternative email
        code = await db.account.add_email_verification(email=data.alternative_email, account_id=account_id,
                                                       student_card_id=None)
        await email.verification.send(to=data.alternative_email, code=code)
    else:  # 刪掉 alternative email
        await db.account.delete_alternative_email_by_id(account_id=account_id)


@router.delete('/account/{account_id}')
async def delete_account(account_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await db.account.delete(account_id)
