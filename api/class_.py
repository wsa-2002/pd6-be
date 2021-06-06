from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
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
async def browse_class(request: auth.Request) -> Sequence[do.Class]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    classes = await db.class_.browse(only_enabled=show_limited, exclude_hidden=show_limited)
    return classes


@router.get('/class/{class_id}')
async def read_class(class_id: int, request: auth.Request) -> do.Class:
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
async def edit_class(class_id: int, data: EditClassInput, request: auth.Request) -> None:
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
async def delete_class(class_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await db.class_.edit(
        class_id=class_id,
        is_enabled=False,
    )


@router.get('/class/{class_id}/member')
async def browse_class_member(class_id: int, request: auth.Request) -> Sequence[do.Member]:
    if not (await rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False)
            or await rbac.validate(request.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    return await db.class_.browse_members(class_id=class_id)


class EditClassMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/class/{class_id}/member')
async def edit_class_member(class_id: int, data: Sequence[EditClassMemberInput], request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    for (member_id, role) in data:
        await db.class_.edit_member(class_id=class_id, member_id=member_id, role=role)


@router.delete('/class/{class_id}/member/{member_id}')
async def delete_class_member(class_id: int, member_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await db.class_.delete_member(class_id=class_id, member_id=member_id)


class AddTeamInput(BaseModel):
    name: str
    is_enabled: bool
    is_hidden: bool


@dataclass
class AddTeamOutput:
    id: int


@router.post('/class/{class_id}/team', tags=['Team'])
async def add_team_under_class(class_id: int, data: AddTeamInput, request: auth.Request) -> AddTeamOutput:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    team_id = await db.team.add(
        name=data.name,
        class_id=class_id,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )

    return AddTeamOutput(id=team_id)


@router.get('/class/{class_id}/team', tags=['Team'])
async def browse_team_under_class(class_id: int, request: auth.Request) -> Sequence[do.Team]:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    return await db.team.browse(class_id=class_id)
