from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from pydantic import BaseModel

from base import do, enum, popo
from base.enum import RoleType, FilterOperator
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model


router = APIRouter(
    tags=['Class'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


BROWSE_CLASS_COLUMNS = {
    'id': int,
    'name': str,
    'course_id': int,
    'is_deleted': bool,
}


@router.get('/class')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_COLUMNS.items()})
async def browse_class(
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - system normal: all

    ### Available columns
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CLASS_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_COLUMNS)

    classes, total_count = await service.class_.browse_with_filter(limit=limit, offset=offset,
                                                                   filters=filters, sorters=sorters)
    return model.BrowseOutputBase(classes, total_count=total_count)


@router.get('/class/{class_id}')
@enveloped
async def read_class(class_id: int, request: Request) -> do.Class:
    """
    ### 權限
    - System normal: all
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await service.class_.read(class_id=class_id)


class EditClassInput(BaseModel):
    name: str = None
    course_id: int = None


@router.patch('/class/{class_id}')
@enveloped
async def edit_class(class_id: int, data: EditClassInput, request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await service.class_.edit(
        class_id=class_id,
        name=data.name,
        course_id=data.course_id,
    )


@router.delete('/class/{class_id}')
@enveloped
async def delete_class(class_id: int, request: Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await service.class_.delete(class_id)


@dataclass
class BrowseClassMemberOutput:
    member_id: int
    role: enum.RoleType
    username: str
    real_name: str
    student_id: str
    institute_abbreviated_name: str


BROWSE_CLASS_MEMBER_COLUMNS = {
    'member_id': int,
    'class_id': int,
    'role': enum.RoleType,
}


@router.get('/class/{class_id}/member')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_MEMBER_COLUMNS.items()})
async def browse_class_member(
        class_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - Class normal
    - Class+ manager

    ### Available columns
    """
    if (not await rbac.validate(request.account.id, RoleType.normal, class_id=class_id)
            and not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CLASS_MEMBER_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_MEMBER_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    result, total_count = await service.class_.browse_member_account_with_student_card_and_institute(
                                               limit=limit, offset=offset, filters=filters, sorters=sorters)
    data = [BrowseClassMemberOutput(member_id=member.member_id, role=member.role,
                                    username=account.username, real_name=account.real_name,
                                    student_id=student_card.student_id,
                                    institute_abbreviated_name=institute.abbreviated_name)
            for member, account, student_card, institute in result]
    return model.BrowseOutputBase(data, total_count=total_count)


@dataclass
class ReadClassMemberOutput:
    member_id: Optional[int]
    member_referral: Optional[str]


@router.get('/class/{class_id}/member/account-referral')
@enveloped
async def browse_all_class_member_with_account_referral(class_id: int, request: Request) \
        -> Sequence[ReadClassMemberOutput]:
    """
    ### 權限
    - Class normal
    - Class+ manager
    """
    if (not await rbac.validate(request.account.id, RoleType.normal, class_id=class_id)
            and not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)):
        raise exc.NoPermission

    results = await service.class_.browse_class_member_with_account_referral()
    return [ReadClassMemberOutput(member_id=member.member_id,
                                  member_referral=member_referral)
            for (member, member_referral) in results]


class EditClassMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/class/{class_id}/member')
@enveloped
async def edit_class_member(class_id: int, data: Sequence[EditClassMemberInput], request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission
    await service.class_.edit_member(class_id=class_id,
                                     member_roles=[(member.member_id, member.role) for member in data],
                                     operator_id=request.account.id)


class SetClassMemberInput(BaseModel):
    account_referral: str
    role: RoleType


@router.put('/class/{class_id}/member')
@enveloped
async def replace_class_members(class_id: int, data: Sequence[SetClassMemberInput], request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await service.class_.replace_members(class_id=class_id,
                                         member_roles=[(member.account_referral, member.role)
                                                       for member in data],
                                         operator_id=request.account.id)


@router.delete('/class/{class_id}/member/{member_id}')
@enveloped
async def delete_class_member(class_id: int, member_id: int, request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await service.class_.delete_member(class_id=class_id, member_id=member_id)


class AddTeamInput(BaseModel):
    name: str
    label: str


@router.post('/class/{class_id}/team', tags=['Team'])
@enveloped
async def add_team_under_class(class_id: int, data: AddTeamInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    team_id = await service.team.add(
        name=data.name,
        class_id=class_id,
        label=data.label,
    )

    return model.AddOutput(id=team_id)


BROWSE_TEAM_UNDER_CLASS_COLUMNS = {
    'id': int,
    'name': str,
    'class_id': int,
    'label': str,
    'is_deleted': bool,
}


@router.get('/class/{class_id}/team', tags=['Team'])
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_TEAM_UNDER_CLASS_COLUMNS.items()})
async def browse_team_under_class(
        class_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - Class normal: all

    ### Available columns
    """
    class_role = await rbac.get_role(request.account.id, class_id=class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_TEAM_UNDER_CLASS_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_TEAM_UNDER_CLASS_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))
    teams, total_count = await service.team.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)
    return model.BrowseOutputBase(teams, total_count=total_count)


BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS = {
    'id': int,
    'account_id': int,
    'problem_id': int,
    'language_id': int,
    'content_file_uuid': UUID,
    'content_length': int,
    'filename': str,
    'submit_time': model.ServerTZDatetime,
}


@router.get('/class/{class_id}/submission', tags=['Submission'])
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS.items()})
async def browse_submission_under_class(
        class_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - Class manager

    ### Available columns
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)

    submissions, total_count = await service.submission.browse_under_class(class_id=class_id,
                                                                           limit=limit, offset=offset,
                                                                           filters=filters, sorters=sorters)
    return model.BrowseOutputBase(submissions, total_count=total_count)
