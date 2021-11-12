from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import service
from persistence import email

from .util import rbac

router = APIRouter(
    tags=['Student Card'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddStudentCardInput(BaseModel):
    institute_id: int
    institute_email_prefix: str
    student_id: str


@router.post('/account/{account_id}/student-card', tags=['Account'])
@enveloped
async def add_student_card_to_account(account_id: int, data: AddStudentCardInput, request: Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id == account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    try:
        institute = await db.institute.read(data.institute_id, include_disabled=False)
    except exc.persistence.NotFound:
        raise exc.account.InvalidInstitute

    if data.student_id.lower() != data.institute_email_prefix.lower():
        raise exc.account.StudentIdNotMatchEmail

    if await db.student_card.is_duplicate(institute.id, data.student_id):
        raise exc.account.StudentCardExists

    institute_email = f"{data.institute_email_prefix}@{institute.email_domain}"
    code = await db.account.add_email_verification(email=institute_email, account_id=account_id,
                                                   institute_id=data.institute_id, student_id=data.student_id)
    account = await db.account.read(account_id)
    await email.verification.send(to=institute_email, code=code, username=account.username)


@router.get('/account/{account_id}/student-card', tags=['Account'])
@enveloped
async def browse_all_account_student_card(account_id: int, request: Request, ) -> Sequence[do.StudentCard]:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id == account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    student_cards = await db.student_card.browse(account_id=account_id)

    return student_cards


@router.get('/student-card/{student_card_id}')
@enveloped
async def read_student_card(student_card_id: int, request: Request) -> do.StudentCard:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = request.account.id == owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    return await db.student_card.read(student_card_id=student_card_id)
