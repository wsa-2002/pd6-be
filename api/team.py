from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Team'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


@router.get('/team/{team_id}')
@enveloped
async def read_team(team_id: int, request: auth.Request) -> do.Team:
    """
    ### 權限
    - Class normal (not hidden)
    - Class manager (hidden)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await db.team.read(team_id, include_hidden=True)

    class_role = await rbac.get_role(request.account.id, class_id=team.class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    if team.is_hidden and class_role < RoleType.manager:
        raise exc.NoPermission

    return team


class EditTeamInput(BaseModel):
    name: str = None
    class_id: int = None
    label: str = None
    is_hidden: bool = None


@router.patch('/team/{team_id}')
@enveloped
async def edit_team(team_id: int, data: EditTeamInput, request: auth.Request) -> None:
    """
    ### 權限
    - Class manager
    - Team manager (limited)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await db.team.read(team_id, include_hidden=True)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id)
    is_team_manager = await rbac.validate(request.account.id, RoleType.manager, team_id=team_id)

    if not is_class_manager and not is_team_manager:
        raise exc.NoPermission

    # 不是 CM 但卻碰了不該碰的東西
    if not is_class_manager and (
            data.is_hidden is not None
            or data.class_id is not None
    ):
        raise exc.NoPermission

    await db.team.edit(
        team_id=team_id,
        name=data.name,
        class_id=data.class_id,
        is_hidden=data.is_hidden,
        label=data.label,
    )


@router.delete('/team/{team_id}')
@enveloped
async def delete_team(team_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await db.team.read(team_id, include_hidden=True)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=team.id):
        raise exc.NoPermission

    await db.team.delete(team_id)


@router.get('/team/{team_id}/member')
@enveloped
async def browse_team_member(team_id: int, request: auth.Request) -> Sequence[do.Member]:
    """
    ### 權限
    - Class normal
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await db.team.read(team_id, include_hidden=True)

    if not await rbac.validate(request.account.id, RoleType.normal, class_id=team.class_id):
        raise exc.NoPermission

    member_roles = await db.team.browse_members(team_id=team_id)
    return member_roles


class EditMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/team/{team_id}/member')
@enveloped
async def edit_team_member(team_id: int, data: Sequence[EditMemberInput], request: auth.Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await db.team.read(team_id, include_hidden=True)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id):
        raise exc.NoPermission

    for (member_id, role) in data:
        await db.team.edit_member(team_id=team_id, member_id=member_id, role=role)


@router.delete('/team/{team_id}/member/{member_id}')
@enveloped
async def delete_team_member(team_id: int, member_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await db.team.read(team_id, include_hidden=True)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=team.class_id):
        raise exc.NoPermission

    await db.team.delete_member(team_id=team_id, member_id=member_id)
