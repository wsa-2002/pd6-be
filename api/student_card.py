# TODO: Rewrite this whole stuff?

from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import persistence.email as email
from util import rbac

router = APIRouter(
    tags=['Student Card'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


class AddStudentCardInput(BaseModel):
    institute_id: int
    institute_email_prefix: str
    department: str
    student_id: str


@router.post('/account/{account_id}/student-card', tags=['Account'])
@enveloped
async def add_student_card_to_account(account_id: int, data: AddStudentCardInput, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    try:
        institute = await db.institute.read(data.institute_id, include_disabled=False)
    except exc.NotFound:
        raise exc.InvalidInstitute

    if data.student_id != data.institute_email_prefix:
        raise exc.EmailNotMatch
    
    institute_email = f"{data.institute_email_prefix}@{institute.email_domain}"
    code = await db.account.add_email_verification(email=institute_email, account_id=account_id,
                                                   institute_id=data.institute_id, department=data.department, student_id=data.student_id)
    await email.verification.send(to=institute_email, code=code)


@router.get('/account/{account_id}/student-card', tags=['Account'])
@enveloped
async def browse_account_student_card(account_id: int, request: auth.Request) -> Sequence[do.StudentCard]:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    return await db.student_card.browse(account_id)


@router.get('/student-card/{student_card_id}')
@enveloped
async def read_student_card(student_card_id: int, request: auth.Request) -> do.StudentCard:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = request.account.id is owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    return await db.student_card.read(student_card_id=student_card_id)


# can only edit department!
class EditStudentCardInput(BaseModel):
    department: str = None


@router.patch('/student-card/{student_card_id}')
@enveloped
async def edit_student_card(student_card_id: int, data: EditStudentCardInput, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = request.account.id is owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await db.student_card.edit(
        student_card_id=student_card_id,
        department=data.department,
    )
