from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import persistence.email as email
from util import rbac


router = APIRouter(
    tags=['Class'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


@router.get('/class')
@enveloped
async def browse_class(request: auth.Request) -> Sequence[do.Class]:
    """
    ### 權限
    - Class+ manager (hidden)
    - System normal (not hidden)
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    classes = set()  # FIXME: 其實不可以 set QQ
    classes.update(await db.class_.browse_from_member_role(member_id=request.account.id, role=RoleType.manager,
                                                           include_hidden=True))  # classes as manager
    classes.update(await db.class_.browse(include_hidden=False))  # normal classes

    # 這邊多 sort 了一次！
    def sorter(class_: do.Class): return class_.course_id, class_.id
    return sorted(classes, key=sorter)


@router.get('/class/{class_id}')
@enveloped
async def read_class(class_id: int, request: auth.Request) -> do.Class:
    """
    ### 權限
    - Class+ manager (hidden)
    - System normal (not hidden)
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)

    class_ = await db.class_.read(class_id=class_id, include_hidden=is_class_manager)
    return class_


class EditClassInput(BaseModel):
    name: str = None
    course_id: int = None
    is_hidden: bool = None


@router.patch('/class/{class_id}')
@enveloped
async def edit_class(class_id: int, data: EditClassInput, request: auth.Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await db.class_.edit(
        class_id=class_id,
        name=data.name,
        course_id=data.course_id,
        is_hidden=data.is_hidden,
    )


@router.delete('/class/{class_id}')
@enveloped
async def delete_class(class_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.class_.delete(class_id)


@router.get('/class/{class_id}/member')
@enveloped
async def browse_class_member(class_id: int, request: auth.Request) -> Sequence[do.Member]:
    """
    ### 權限
    - Class normal
    - Class+ manager
    """
    if (not await rbac.validate(request.account.id, RoleType.normal, class_id=class_id)
            and not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)):
        raise exc.NoPermission

    return await db.class_.browse_members(class_id=class_id)


class EditClassMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/class/{class_id}/member')
@enveloped
async def edit_class_member(class_id: int, data: Sequence[EditClassMemberInput], request: auth.Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    for (member_id, role) in data:
        if role == RoleType.manager and not await rbac.validate(member_id, RoleType.manager,
                                                                class_id=class_id, inherit=True):  # add CM
            await email.notification.notify_cm_change([], member_id, class_id, request.account.id)
        await db.class_.edit_member(class_id=class_id, member_id=member_id, role=role)


@router.delete('/class/{class_id}/member/{member_id}')
@enveloped
async def delete_class_member(class_id: int, member_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await db.class_.delete_member(class_id=class_id, member_id=member_id)


class AddTeamInput(BaseModel):
    name: str
    label: str
    is_hidden: bool


@dataclass
class AddTeamOutput:
    id: int


@router.post('/class/{class_id}/team', tags=['Team'])
@enveloped
async def add_team_under_class(class_id: int, data: AddTeamInput, request: auth.Request) -> AddTeamOutput:
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    team_id = await db.team.add(
        name=data.name,
        class_id=class_id,
        label=data.label,
        is_hidden=data.is_hidden,
    )

    return AddTeamOutput(id=team_id)


@router.get('/class/{class_id}/team', tags=['Team'])
@enveloped
async def browse_team_under_class(class_id: int, request: auth.Request) -> Sequence[do.Team]:
    """
    ### 權限
    - Class normal (not hidden)
    - Class manager (hidden)
    """
    class_role = await rbac.get_role(request.account.id, class_id=class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    return await db.team.browse(class_id=class_id, include_hidden=class_role >= RoleType.manager)
