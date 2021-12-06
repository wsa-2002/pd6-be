from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from util import model
from util.context import context

router = APIRouter(
    tags=['Institute'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddInstituteInput(BaseModel):
    abbreviated_name: str
    full_name: str
    email_domain: str
    is_disabled: bool


@router.post('/institute')
@enveloped
async def add_institute(data: AddInstituteInput) -> model.AddOutput:
    """
    ### 權限
    - System Manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    institute_id = await db.institute.add(abbreviated_name=data.abbreviated_name, full_name=data.full_name,
                                          email_domain=data.email_domain, is_disabled=data.is_disabled)
    return model.AddOutput(id=institute_id)


@router.get('/institute', tags=['Public'])
@enveloped
async def browse_all_institute() -> Sequence[do.Institute]:
    """
    ### 權限
    - Public
    """
    return await db.institute.browse()


@router.get('/institute/{institute_id}', tags=['Public'])
@enveloped
async def read_institute(institute_id: int) -> do.Institute:
    """
    ### 權限
    - Public
    """
    return await db.institute.read(institute_id)


class EditInstituteInput(BaseModel):
    abbreviated_name: str = None
    full_name: str = None
    email_domain: str = None
    is_disabled: bool = None


@router.patch('/institute/{institute_id}')
@enveloped
async def edit_institute(institute_id: int, data: EditInstituteInput) -> None:
    """
    ### 權限
    - System Manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.institute.edit(
        institute_id=institute_id,
        abbreviated_name=data.abbreviated_name,
        full_name=data.full_name,
        email_domain=data.email_domain,
        is_disabled=data.is_disabled,
    )
