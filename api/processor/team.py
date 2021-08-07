from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
from util import rbac

from .. import service


router = APIRouter(
    tags=['Team'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


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


@router.get('/team/{team_id}/member')
@enveloped
async def browse_team_member(team_id: int, request: Request) -> Sequence[do.Member]:
    """
    ### 權限
    - Class normal
    """
    # 因為需要 class_id 才能判斷權限，所以先 read team 再判斷要不要噴 NoPermission
    team = await service.team.read(team_id)

    if not await rbac.validate(request.account.id, RoleType.normal, class_id=team.class_id):
        raise exc.NoPermission

    return await service.team.browse_members(team_id=team_id)


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

    for (member_id, role) in data:
        await service.team.edit_member(team_id=team_id, member_id=member_id, role=role)


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
