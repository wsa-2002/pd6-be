# TODO: Rewrite this whole stuff?

from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac

router = APIRouter(
    tags=['Student Card'],
    default_response_class=envelope.JSONResponse,
)


class AddStudentCardInput(BaseModel):
    institute_id: int
    department: str
    student_id: str
    email: str


@dataclass
class AddStudentCardOutput:
    id: int


@router.post('/account/{account_id}/student-card', tags=['Account'])
async def add_student_card_to_account(account_id: int, data: AddStudentCardInput, request: auth.Request) \
        -> AddStudentCardOutput:
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    student_card_id = await db.student_card.add(
        account_id=account_id,
        institute_id=data.institute_id,
        department=data.department,
        student_id=data.student_id,
        email=data.email,
    )
    return AddStudentCardOutput(id=student_card_id)


@router.get('/account/{account_id}/student-card', tags=['Account'])
async def browse_account_student_card(account_id: int, request: auth.Request) -> Sequence[do.StudentCard]:
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    return await db.student_card.browse(account_id)


@router.get('/student-card/{student_card_id}')
async def read_student_card(student_card_id: int, request: auth.Request) -> do.StudentCard:
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = request.account.id is owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    return await db.student_card.read(student_card_id=student_card_id)


class EditStudentCardInput(BaseModel):
    institute_id: int = None
    department: str = None
    student_id: str = None
    email: str = None


@router.patch('/student-card/{student_card_id}')
async def edit_student_card(student_card_id: int, data: EditStudentCardInput, request: auth.Request) -> None:
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = request.account.id is owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await db.student_card.edit(
        student_card_id=student_card_id,
        institute_id=data.institute_id,
        department=data.department,
        student_id=data.student_id,
        email=data.email,
    )


@router.delete('/student-card/{student_card_id}')
async def delete_student_card(student_card_id: int, request: auth.Request) -> None:
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = request.account.id is owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await db.student_card.delete(student_card_id)
