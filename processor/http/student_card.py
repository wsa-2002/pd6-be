from typing import Sequence

import pydantic
from pydantic import BaseModel, constr

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from persistence import email
import service
from util import model
from util.context import context

router = APIRouter(
    tags=['Student Card'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddStudentCardInput(BaseModel):
    institute_id: int
    institute_email_prefix: constr(to_lower=True)
    student_id: constr(to_lower=True)


@router.post('/account/{account_id}/student-card', tags=['Account'])
@enveloped
async def add_student_card_to_account(account_id: int, data: AddStudentCardInput) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    is_self = context.account.id == account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    try:
        institute = await db.institute.read(data.institute_id, include_disabled=False)
    except exc.persistence.NotFound:
        raise exc.account.InvalidInstitute

    if data.student_id != data.institute_email_prefix:
        raise exc.account.StudentIdNotMatchEmail

    if await db.student_card.is_duplicate(institute.id, data.student_id):
        raise exc.account.StudentCardExists

    institute_email = f"{data.institute_email_prefix}@{institute.email_domain}"
    try:
        institute_email = pydantic.parse_obj_as(model.CaseInsensitiveEmailStr, institute_email)
    except pydantic.EmailError as e:
        raise exc.account.InvalidEmail from e

    code = await db.account.add_email_verification(email=institute_email, account_id=account_id,
                                                   institute_id=data.institute_id, student_id=data.student_id)
    account = await db.account.read(account_id)
    await email.verification.send(to=institute_email, code=code, username=account.username)


@router.get('/account/{account_id}/student-card', tags=['Account'])
@enveloped
async def browse_all_account_student_card(account_id: int, ) -> Sequence[do.StudentCard]:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    is_self = context.account.id == account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    student_cards = await db.student_card.browse(account_id=account_id)

    return student_cards


@router.get('/student-card/{student_card_id}')
@enveloped
async def read_student_card(student_card_id: int) -> do.StudentCard:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    owner_id = await db.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = context.account.id == owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    return await db.student_card.read(student_card_id=student_card_id)
