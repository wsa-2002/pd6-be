from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from fastapi import UploadFile, File
from pydantic import BaseModel

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from util.context import context

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
async def import_team(class_id: int, label: str, team_file: UploadFile = File(...)) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await service.csv.import_team(team_file.file, class_id=class_id, label=label)


@router.get('/team/template')
@enveloped
async def get_team_template_file() -> GetTeamTemplateOutput:
    """
    ### 權限
    - system normal
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    s3_file, filename = await service.csv.get_team_template()
    return GetTeamTemplateOutput(s3_file_uuid=s3_file.uuid, filename=filename)


@router.get('/team/{team_id}')
@enveloped
async def read_team(team_id: int) -> do.Team:
    """
    ### 權限
    - Class normal
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.normal, team_id=team_id):
        raise exc.NoPermission

    return await db.team.read(team_id)


class EditTeamInput(BaseModel):
    name: str = None
    class_id: int = None
    label: str = None


@router.patch('/team/{team_id}')
@enveloped
async def edit_team(team_id: int, data: EditTeamInput) -> None:
    """
    ### 權限
    - Class manager
    - Team manager (limited)
    """
    is_class_manager = await service.rbac.validate_class(context.account.id, RoleType.manager, team_id=team_id)
    is_team_manager = await service.rbac.validate_team(context.account.id, RoleType.manager, team_id=team_id)

    if not is_class_manager and not is_team_manager:
        raise exc.NoPermission

    await db.team.edit(
        team_id=team_id,
        name=data.name,
        class_id=data.class_id,
        label=data.label,
    )


@router.delete('/team/{team_id}')
@enveloped
async def delete_team(team_id: int) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, team_id=team_id):
        raise exc.NoPermission

    await db.team.delete(team_id)


@router.get('/team/{team_id}/member')
@enveloped
async def browse_team_all_member(team_id: int, ) -> Sequence[do.TeamMember]:
    """
    ### 權限
    - Class normal
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.normal, team_id=team_id):
        raise exc.NoPermission

    return await db.team.browse_members(team_id=team_id)


class AddMemberInput(BaseModel):
    account_referral: str
    role: RoleType


@router.post('/team/{team_id}/member')
@enveloped
async def add_team_member(team_id: int, data: Sequence[AddMemberInput]) -> Sequence[bool]:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, team_id=team_id):
        raise exc.NoPermission

    return await db.team.add_members(team_id=team_id,
                                     member_roles=[(member.account_referral, member.role)
                                                   for member in data])


class EditMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/team/{team_id}/member')
@enveloped
async def edit_team_member(team_id: int, data: Sequence[EditMemberInput]) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, team_id=team_id):
        raise exc.NoPermission

    for member in data:
        await db.team.edit_member(team_id=team_id, member_id=member.member_id, role=member.role)


@router.delete('/team/{team_id}/member/{member_id}')
@enveloped
async def delete_team_member(team_id: int, member_id: int) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, team_id=team_id):
        raise exc.NoPermission

    await db.team.delete_member(team_id=team_id, member_id=member_id)
