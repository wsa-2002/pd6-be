from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
import persistence.email as email


router = APIRouter(
    tags=['Account'],
    default_response_class=envelope.JSONResponse,
)


@dataclass
class ReadAccountOutput:
    id: int
    name: str
    nickname: str
    role: str
    real_name: str
    alternative_email: Optional[str]


@router.get('/account/{account_id}')
async def read_account(account_id: int, request: auth.Request) -> ReadAccountOutput:
    ask_for_self = request.account.id == account_id
    if request.account.role.is_guest and not ask_for_self:
        raise exc.NoPermission

    super_access = ask_for_self or request.account.role.is_manager

    target_account = await db.account.read(account_id, include_deleted=super_access)
    result = ReadAccountOutput(
        id=target_account.id,
        name=target_account.name,
        nickname=target_account.nickname,
        role=target_account.role,
        real_name=target_account.real_name if super_access else None,
        alternative_email=target_account.alternative_email if super_access else None,
    )

    return result


class EditAccountInput(BaseModel):
    nickname: str = None
    alternative_email: str = None


@router.patch('/account/{account_id}')
async def edit_account(account_id: int, data: EditAccountInput, request: auth.Request) -> None:
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    # 不檢查 if data.nickname，因為 nickname 可以被刪掉 (設成 None)
    await db.account.edit(account_id=account_id, nickname=data.nickname)

    if data.alternative_email:  # 加或改 alternative email
        code = await db.account.add_email_verification(email=data.alternative_email, account_id=account_id,
                                                       student_card_id=None)
        await email.verification.send(to=data.alternative_email, code=code)
    else:  # 刪掉 alternative email
        await db.account.delete_alternative_email_by_id(account_id=account_id)


@router.delete('/account/{account_id}')
async def delete_account(account_id: int, request: auth.Request) -> None:
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    await db.account.delete(account_id)


class AddInstituteInput(BaseModel):
    name: str
    email_domain: str
    is_disabled: bool


@dataclass
class AddInstituteOutput:
    id: int


@router.post('/institute')
async def add_institute(data: AddInstituteInput, request: auth.Request) -> AddInstituteOutput:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    institute_id = await db.institute.add(name=data.name, email_domain=data.email_domain, is_disabled=data.is_disabled)
    return AddInstituteOutput(id=institute_id)


@router.get('/institute', tags=['Public'])
async def browse_institute(request: auth.Request) -> Sequence[do.Institute]:
    try:
        include_disabled = request.account.role.is_manager
    except exc.NoPermission:
        include_disabled = False

    return await db.institute.browse(include_disabled=include_disabled)


@router.get('/institute/{institute_id}')
async def read_institute(institute_id: int, request: auth.Request) -> do.Institute:
    return await db.institute.read(institute_id, include_disabled=request.account.role.is_manager)


class EditInstituteInput(BaseModel):
    name: str = None
    email_domain: str = None
    is_disabled: bool = None


@router.patch('/institute/{institute_id}')
async def edit_institute(institute_id: int, data: EditInstituteInput, request: auth.Request) -> None:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    await db.institute.edit(
        institute_id=institute_id,
        name=data.name,
        email_domain=data.email_domain,
        is_disabled=data.is_disabled,
    )


# TODO: Student card 機制調整


class AddStudentCardInput(BaseModel):
    institute_id: int
    department: str
    student_id: str
    email: str


@dataclass
class AddStudentCardOutput:
    id: int


@router.post('/account/{account_id}/student-card')
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


@router.get('/account/{account_id}/student-card')
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
    institute_id: int = None
    department: str = None
    student_id: str = None
    email: str = None


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
    )


@router.delete('/student-card/{student_card_id}')
async def delete_student_card(student_card_id: int, request: auth.Request) -> None:
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    if request.account.role.not_manager and request.account.id != owner_id:
        raise exc.NoPermission

    await db.student_card.delete(student_card_id)
