from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from fastapi import UploadFile, File
from pydantic import BaseModel

from base import do, popo
from base.enum import RoleType, FilterOperator
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model


router = APIRouter(
    tags=['Team'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class GetTeamTemplateOutput:
    s3_file_uuid: UUID
    filename: str


@router.post('/class/{class_id}/team-import', tags=['Class'])
@enveloped
async def import_team(class_id: int, request: Request, team_file: UploadFile = File(...)):
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await service.team.import_team(team_file.file, class_id=class_id)


@router.get('/team/template')
@enveloped
async def get_team_template_file(request: Request) -> GetTeamTemplateOutput:
    """
    ### 權限
    - system normal
    """
    if not rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    s3_file, filename = await service.team.get_template_file()
    return GetTeamTemplateOutput(s3_file_uuid=s3_file.uuid, filename=filename)


@router.get('/team/{team_id}')
@enveloped
async def read_team(team_id: int, request: Request) -> do.Team:
    """
    ### 權限
    - Class normal (not hidden)
    - Class manager (hidden)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await service.team.read(team_id)

    class_role = await rbac.get_role(request.account.id, class_id=team.class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    return team


class EditTeamInput(BaseModel):
    name: str = None
    class_id: int = None
    label: str = None


@router.patch('/team/{team_id}')
@enveloped
async def edit_team(team_id: int, data: EditTeamInput, request: Request) -> None:
    """
    ### 權限
    - Class manager
    - Team manager (limited)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await service.team.read(team_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id)
    is_team_manager = await rbac.validate(request.account.id, RoleType.manager, team_id=team_id)

    if not is_class_manager and not is_team_manager:
        raise exc.NoPermission

    await service.team.edit(
        team_id=team_id,
        name=data.name,
        class_id=data.class_id,
        label=data.label,
    )


@router.delete('/team/{team_id}')
@enveloped
async def delete_team(team_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await service.team.read(team_id)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id):
        raise exc.NoPermission

    await service.team.delete(team_id)


BROWSE_TEAM_MEMBER_COLUMNS = {
    'member_id': int,
    'role': RoleType,
}


@router.get('/team/{team_id}/member')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_TEAM_MEMBER_COLUMNS.items()})
async def browse_team_member(team_id: int, request: Request,
                             limit: model.Limit = 50, offset: model.Offset = 0,
                             filter: model.FilterStr = None, sorter: model.SorterStr = None) \
        -> model.BrowseOutputBase:
    """
    ### 權限
    - Class normal

    ### Available columns
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await service.team.read(team_id)

    if not await rbac.validate(request.account.id, RoleType.normal, class_id=team.class_id):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_TEAM_MEMBER_COLUMNS)
    sorters = model.parse_sorter(sorter, BROWSE_TEAM_MEMBER_COLUMNS)

    filters.append(popo.Filter(col_name='team_id',
                               op=FilterOperator.eq,
                               value=team_id))

    team_members, total_count = await service.team.browse_members(limit=limit, offset=offset,
                                                                  filters=filters, sorters=sorters)
    return model.BrowseOutputBase(team_members, total_count=total_count)


class AddMemberInput(BaseModel):
    account_referral: str
    role: RoleType


@router.post('/team/{team_id}/member')
@enveloped
async def add_team_member(team_id: int, data: Sequence[AddMemberInput], request: Request):
    """
    ### 權限
    - class manager
    """
    team = await service.team.read(team_id=team_id)
    if not rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id):
        raise exc.NoPermission
    for member in data:
        await service.team.add_member(team_id=team.id, account_referral=member.account_referral, role=member.role)


class EditMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/team/{team_id}/member')
@enveloped
async def edit_team_member(team_id: int, data: Sequence[EditMemberInput], request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await service.team.read(team_id)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id):
        raise exc.NoPermission

    for member in data:
        await service.team.edit_member(team_id=team_id, member_id=member.member_id, role=member.role)


@router.delete('/team/{team_id}/member/{member_id}')
@enveloped
async def delete_team_member(team_id: int, member_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await service.team.read(team_id)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id):
        raise exc.NoPermission

    await service.team.delete_member(team_id=team_id, member_id=member_id)
