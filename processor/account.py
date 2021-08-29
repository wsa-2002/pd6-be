from fastapi import Query
from dataclasses import dataclass
from typing import Sequence, Optional, List

from pydantic import BaseModel

from base.enum import RoleType
from base import do
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model


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


BROWSE_ACCOUNT_COLUMNS = {
    'id': int,
    'username': str,
    'nickname': str,
    'role': str,
    'real_name': str,
    'alternative_email': str,
}


@router.get('/account')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCOUNT_COLUMNS.items()})
async def browse_account_with_default_student_id(
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - System Manager
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    if not is_manager:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ACCOUNT_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ACCOUNT_COLUMNS)

    result, total_count = await service.account.browse_with_default_student_card(limit=limit, offset=offset,
                                                                                 filters=filters, sorters=sorters)
    data = [BrowseAccountOutput(id=account.id, username=account.username, nickname=account.nickname,
                                role=account.role, real_name=account.real_name,
                                alternative_email=account.alternative_email, student_id=student_card.student_id)
            for account, student_card in result]

    return model.BrowseOutputBase(data, total_count=total_count)


@dataclass
class BatchGetAccountOutput:
    id: int
    username: str
    real_name: str

    student_id: Optional[str]


@router.get('/account-summary/batch')
@enveloped
async def batch_get_account_with_default_student_id(request: Request, account_ids: List[int] = Query(None)) \
        -> Sequence[BatchGetAccountOutput]:
    """
    ### 權限
    - System Normal
    """
    is_normal = await rbac.validate(request.account.id, RoleType.normal)
    if not is_normal:
        raise exc.NoPermission

    result = await service.account.browse_list_with_default_student_card(account_ids=account_ids)
    return [BatchGetAccountOutput(id=account.id, username=account.username, real_name=account.real_name,
                                  student_id=student_card.student_id)
            for account, student_card in result]

@dataclass
class BrowseAccountWithRoleOutput:
    member_id: int
    role: RoleType
    class_id: int
    class_name: str
    course_id: int
    course_name: str


@router.get('/account/{account_id}/class')
@enveloped
async def browse_all_account_with_class_role(account_id: int, request: Request) \
        -> Sequence[BrowseAccountWithRoleOutput]:
    """
    ### 權限
    - Self

    ### Available columns
    """
    if account_id is not request.account.id:
        raise exc.NoPermission
    results = await service.account.browse_with_class_role(account_id=account_id)

    return [BrowseAccountWithRoleOutput(member_id=class_member.member_id,
                                        role=class_member.role,
                                        class_id=class_member.class_id,
                                        class_name=class_.name,
                                        course_id=course.id,
                                        course_name=course.name)
            for class_member, class_, course in results]


@dataclass
class ReadAccountOutput:
    id: int
    username: str
    nickname: str
    role: str
    real_name: str
    alternative_email: Optional[str]

    student_id: Optional[str]


@router.get('/account/{account_id}')
@enveloped
async def read_account_with_default_student_id(account_id: int, request: Request) -> ReadAccountOutput:
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

    account, student_card = await service.account.read_with_default_student_card(account_id=account_id)
    result = ReadAccountOutput(
        id=account.id,
        username=account.username,
        nickname=account.nickname,
        role=account.role,
        real_name=account.real_name if view_personal else None,
        alternative_email=account.alternative_email if view_personal else None,
        student_id=student_card.student_id if view_personal else None,
    )

    return result


class EditAccountInput(BaseModel):
    nickname: str = None
    alternative_email: str = model.can_omit
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
