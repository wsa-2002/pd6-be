from typing import Sequence

from pydantic import BaseModel

from base import do, popo
import exceptions as exc
from base.enum import RoleType, FilterOperator
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model


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
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    try:
        institute = await service.institute.read(data.institute_id, include_disabled=False)
    except exc.persistence.NotFound:
        raise exc.account.InvalidInstitute

    if data.student_id != data.institute_email_prefix:
        raise exc.account.StudentIdNotMatchEmail

    if service.student_card.is_duplicate(institute.id, data.student_id):
        raise exc.account.StudentCardExists

    institute_email = f"{data.institute_email_prefix}@{institute.email_domain}"
    await service.student_card.add(account_id=account_id, institute_email=institute_email,
                                   institute_id=institute.id, student_id=data.student_id)


BROWSE_STUDENT_CARD_COLUMNS = {
    'institute_id': int,
    'student_id': str,
    'email': str,
}


@router.get('/account/{account_id}/student-card', tags=['Account'])
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_STUDENT_CARD_COLUMNS.items()})
async def browse_account_student_card(account_id: int, request: Request,
                                      limit: model.Limit = 50, offset: model.Offset = 0,
                                      filter: model.FilterStr = None, sort: model.SorterStr = None,
                                      ) -> model.BrowseOutputBase:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    is_self = request.account.id is account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_STUDENT_CARD_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_STUDENT_CARD_COLUMNS)
    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=account_id))

    student_cards, total_count = await service.student_card.browse(limit=limit, offset=offset,
                                                                   filters=filters, sorters=sorters)

    return model.BrowseOutputBase(student_cards, total_count=total_count)


@router.get('/student-card/{student_card_id}')
@enveloped
async def read_student_card(student_card_id: int, request: Request) -> do.StudentCard:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    owner_id = await service.student_card.read_owner_id(student_card_id=student_card_id)
    is_self = request.account.id is owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    return await service.student_card.read(student_card_id=student_card_id)
