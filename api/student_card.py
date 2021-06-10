# TODO: Rewrite this whole stuff?

from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db


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
    if request.account.role.not_manager and request.account.id != account_id:
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
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    return await db.student_card.browse(account_id)


@router.get('/student-card/{student_card_id}')
async def read_student_card(student_card_id: int, request: auth.Request) -> do.StudentCard:
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    if request.account.role.not_manager and request.account.id != owner_id:
        raise exc.NoPermission

    return await db.student_card.read(student_card_id=student_card_id)


class EditStudentCardInput(BaseModel):
    institute_id: int
    department: str
    student_id: str
    email: str
    is_enabled: bool


@router.patch('/student-card/{student_card_id}')
async def edit_student_card(student_card_id: int, data: EditStudentCardInput, request: auth.Request) -> None:
    # 暫時只開給 manager
    if not request.account.role.is_manager:
        raise exc.NoPermission

    await db.student_card.edit(
        student_card_id=student_card_id,
        institute_id=data.institute_id,
        department=data.department,
        student_id=data.student_id,
        email=data.email,
        is_enabled=data.is_enabled,
    )


@router.delete('/student-card/{student_card_id}')
async def delete_student_card(student_card_id: int, request: auth.Request) -> None:
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    if request.account.role.not_manager and request.account.id != owner_id:
        raise exc.NoPermission

    await db.student_card.edit(student_card_id, is_enabled=False)
