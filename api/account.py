from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
import persistence.email as email


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
    ask_for_self = request.account.id == account_id
    if request.account.role.is_guest and not ask_for_self:
        raise exc.NoPermission

    super_access = ask_for_self or request.account.role.is_manager

    target_account = await db.account.read(account_id, include_deleted=super_access)
    result = ReadAccountOutput(
        id=target_account.id,
        name=target_account.name,
        nickname=target_account.nickname,
        role=target_account.role,
        real_name=target_account.real_name if super_access else None,
        alternative_email=target_account.alternative_email if super_access else None,
    )

    return result


class EditAccountInput(BaseModel):
    nickname: str = None
    alternative_email: str = None


@router.patch('/account/{account_id}')
async def edit_account(account_id: int, data: EditAccountInput, request: auth.Request) -> None:
    if request.account.role.not_manager and request.account.id != account_id:
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
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    await db.account.delete(account_id)
