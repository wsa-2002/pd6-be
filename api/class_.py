from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do, vo
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import persistence.email as email
from util import rbac


router = APIRouter(
    tags=['Class'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/class')
@enveloped
async def browse_class(request: Request) -> Sequence[do.Class]:
    """
    ### 權限
    - system normal: all
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.class_.browse()


@router.get('/class/{class_id}')
@enveloped
async def read_class(class_id: int, request: Request) -> do.Class:
    """
    ### 權限
    - System normal: all
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.class_.read(class_id=class_id)


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

    await db.class_.edit(
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

    await db.class_.delete(class_id)


@router.get('/class/{class_id}/member')
@enveloped
async def browse_class_member(class_id: int, request: Request) -> Sequence[vo.MemberWithStudentCard]:
    """
    ### 權限
    - Class normal
    - Class+ manager
    """
    if (not await rbac.validate(request.account.id, RoleType.normal, class_id=class_id)
            and not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)):
        raise exc.NoPermission

    return await db.class_vo.browse_member_with_student_card(class_id=class_id)


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

    for item in data:
        await db.class_.edit_member(class_id=class_id, member_id=item.member_id, role=item.role)

    updated_class_managers = [member.member_id for member in data if member.role is RoleType.manager]
    if updated_class_managers:
        class_manager_emails = await db.class_.browse_member_emails(class_id, RoleType.manager)
        await email.notification.notify_cm_change(class_manager_emails, updated_class_managers,
                                                  class_id, request.account.id)


@router.delete('/class/{class_id}/member/{member_id}')
@enveloped
async def delete_class_member(class_id: int, member_id: int, request: Request) -> None:
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


@dataclass
class AddTeamOutput:
    id: int


@router.post('/class/{class_id}/team', tags=['Team'])
@enveloped
async def add_team_under_class(class_id: int, data: AddTeamInput, request: Request) -> AddTeamOutput:
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
    )

    return AddTeamOutput(id=team_id)


@router.get('/class/{class_id}/team', tags=['Team'])
@enveloped
async def browse_team_under_class(class_id: int, request: Request) -> Sequence[do.Team]:
    """
    ### 權限
    - Class normal: all
    """
    class_role = await rbac.get_role(request.account.id, class_id=class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    return await db.team.browse(class_id=class_id)
