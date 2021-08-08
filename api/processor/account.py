from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
from .util import rbac

from .. import service


router = APIRouter(
    tags=['Account'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class BrowseAccountOutput:
    id: int
    username: str
    nickname: str
    role: str
    real_name: str
    alternative_email: Optional[str]

    student_id: Optional[str]


@router.get('/account')
@enveloped
async def browse_account_with_default_student_id(request: Request) -> Sequence[BrowseAccountOutput]:
    """
    ### 權限
    - System Manager
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    if not is_manager:
        raise exc.NoPermission

    result = await service.account.browse_with_default_student_card()
    return [BrowseAccountOutput(id=account.id, username=account.username, nickname=account.nickname,
                                role=account.role, real_name=account.real_name,
                                alternative_email=account.alternative_email, student_id=student_card.student_id)
            for account, student_card in result]


@dataclass
class ReadAccountOutput:
    id: int
    username: str
    nickname: str
    role: str
    real_name: str
    alternative_email: Optional[str]


@router.get('/account/{account_id}')
@enveloped
async def read_account(account_id: int, request: Request) -> ReadAccountOutput:
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

    target_account = await service.account.read(account_id)
    result = ReadAccountOutput(
        id=target_account.id,
        username=target_account.username,
        nickname=target_account.nickname,
        role=target_account.role,
        real_name=target_account.real_name if view_personal else None,
        alternative_email=target_account.alternative_email if view_personal else None,
    )

    return result


class EditAccountInput(BaseModel):
    nickname: str = None
    alternative_email: str = None
    real_name: str = None


@router.patch('/account/{account_id}')
@enveloped
async def edit_account(account_id: int, data: EditAccountInput, request: Request) -> None:
    """
    ### 權限
    - System Manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not ((is_self and not data.real_name) or is_manager):
        raise exc.NoPermission

    await service.account.edit_alternative_email(account_id=account_id, alternative_email=data.alternative_email)

    await service.account.edit_general(account_id=account_id, nickname=data.nickname, real_name=data.real_name)


class EditPasswordInput(BaseModel):
    old_password: Optional[str]
    new_password: str


@router.put('/account/{account_id}/pass_hash')
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


@router.delete('/account/{account_id}')
@enveloped
async def delete_account(account_id: int, request: Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await service.account.delete(account_id=account_id)


class DefaultStudentCardInput(BaseModel):
    student_card_id: int


@router.put('/account/{account_id}/default-student-card')
@enveloped
async def make_student_card_default(account_id: int, data: DefaultStudentCardInput, request: Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    owner_id = await service.student_card.read_owner_id(student_card_id=data.student_card_id)
    if account_id != owner_id:
        raise exc.account.StudentCardDoesNotBelong

    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await service.account.edit_default_student_card(account_id=account_id, student_card_id=data.student_card_id)
