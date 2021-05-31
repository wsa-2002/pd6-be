from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac

router = APIRouter(
    tags=['Team'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/team')
async def get_teams(request: auth.Request) -> Sequence[db.team.do.Team]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    teams = await db.team.browse(only_enabled=show_limited, exclude_hidden=show_limited)
    return teams


@router.get('/team/{team_id}')
async def get_team(team_id: int, request: auth.Request) -> db.team.do.Team:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    team = await db.team.read(team_id, only_enabled=show_limited, exclude_hidden=show_limited)
    return team


async def is_team_manager(team_id, account_id):
    # Check with team role
    try:
        req_account_role = await db.team.read_member_role(team_id=team_id, member_id=account_id)
    except exc.NotFound:  # Not even in team
        return False
    else:
        return req_account_role.is_manager


class ModifyTeamInput(BaseModel):
    name: str
    class_id: int
    is_enabled: bool
    is_hidden: bool


@router.patch('/team/{team_id}')
async def modify_team(team_id: int, data: ModifyTeamInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with team role
    if not await is_team_manager(team_id, request.account.id):
        raise exc.NoPermission

    await db.team.edit(
        team_id=team_id,
        name=data.name,
        class_id=data.class_id,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )


@router.delete('/team/{team_id}')
async def remove_team(team_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with team role
    if not await is_team_manager(team_id, request.account.id):
        raise exc.NoPermission

    await db.team.edit(
        team_id=team_id,
        is_enabled=False,
    )


@dataclass
class TeamMemberOutput:
    member_id: int
    role: RoleType


@router.get('/team/{team_id}/member')
async def get_team_members(team_id: int, request: auth.Request) -> Sequence[TeamMemberOutput]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    try:
        await db.team.read_member_role(team_id=team_id, member_id=request.account.id)
    except exc.NotFound:  # Not even in course
        if not request.account.role.is_manager:  # and is not manager
            raise exc.NoPermission

    member_roles = await db.team.browse_members(team_id=team_id)

    return [TeamMemberOutput(
        member_id=acc_id,
        role=role,
    ) for acc_id, role in member_roles]


class TeamMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/team/{team_id}/member')
async def modify_team_member(team_id: int, data: Sequence[TeamMemberInput], request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with team role
    if not await is_team_manager(team_id, request.account.id):
        raise exc.NoPermission

    for (member_id, role) in data:
        await db.team.edit_member(team_id=team_id, member_id=member_id, role=role)


@router.delete('/team/{team_id}/member/{member_id}')
async def remove_team_member(team_id: int, member_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    await db.team.delete_member(team_id=team_id, member_id=member_id)
