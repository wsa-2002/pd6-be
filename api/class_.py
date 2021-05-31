from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac

router = APIRouter(
    tags=['Class'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/class')
async def get_classes(request: auth.Request) -> Sequence[db.class_.do.Class]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    classes = await db.class_.browse(only_enabled=show_limited, exclude_hidden=show_limited)
    return classes


@router.get('/class/{class_id}')
async def get_class(class_id: int, request: auth.Request) -> db.class_.do.Class:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    class_ = await db.class_.read(class_id=class_id, only_enabled=show_limited, exclude_hidden=show_limited)
    return class_


class EditClassInput(BaseModel):
    name: Optional[str]
    course_id: Optional[int]
    is_enabled: Optional[bool]
    is_hidden: Optional[bool]


@router.patch('/class/{class_id}')
async def modify_class(class_id: int, data: EditClassInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await db.class_.edit(
        class_id=class_id,
        name=data.name,
        course_id=data.course_id,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )


@router.delete('/class/{class_id}')
async def remove_class(class_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await db.class_.edit(
        class_id=class_id,
        is_enabled=False,
    )


@dataclass
class ClassMemberOutput:
    member_id: int
    role: RoleType


@router.get('/class/{class_id}/member')
async def get_class_members(class_id: int, request: auth.Request) -> Sequence[ClassMemberOutput]:
    if not (await rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False)
            or await rbac.validate(request.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    member_roles = await db.class_.browse_members(class_id=class_id)

    return [ClassMemberOutput(
        member_id=acc_id,
        role=role,
    ) for acc_id, role in member_roles]


class ClassMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/class/{class_id}/member')
async def modify_class_member(class_id: int, data: Sequence[ClassMemberInput], request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    for (member_id, role) in data:
        await db.class_.edit_member(class_id=class_id, member_id=member_id, role=role)


@router.delete('/class/{class_id}/member/{member_id}')
async def remove_class_member(class_id: int, member_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await db.class_.delete_member(class_id=class_id, member_id=member_id)


class CreateTeamInput(BaseModel):
    name: str
    is_enabled: bool
    is_hidden: bool


@dataclass
class CreateTeamOutput:
    id: int


@router.post('/class/{class_id}/team', tags=['Team'])
async def create_team_under_class(class_id: int, data: CreateTeamInput, request: auth.Request) -> CreateTeamOutput:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    team_id = await db.team.add(
        name=data.name,
        class_id=class_id,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )

    return CreateTeamOutput(id=team_id)


@router.get('/class/{class_id}/team', tags=['Team'])
async def get_teams_under_class(class_id: int, request: auth.Request) -> Sequence[int]:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    return await db.class_.browse_teams(class_id=class_id)
