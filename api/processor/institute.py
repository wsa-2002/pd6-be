from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth, Request
from .util import rbac

from .. import service

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


@dataclass
class AddInstituteOutput:
    id: int


@router.post('/institute')
@enveloped
async def add_institute(data: AddInstituteInput, request: Request) -> AddInstituteOutput:
    """
    ### 權限
    - System Manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    institute_id = await service.institute.add(abbreviated_name=data.abbreviated_name, full_name=data.full_name,
                                               email_domain=data.email_domain, is_disabled=data.is_disabled)
    return AddInstituteOutput(id=institute_id)


@router.get('/institute', tags=['Public'])
@enveloped
async def browse_institute() -> Sequence[do.Institute]:
    """
    ### 權限
    - Public
    """
    return await service.institute.browse()


@router.get('/institute/{institute_id}', tags=['Public'])
@enveloped
async def read_institute(institute_id: int) -> do.Institute:
    """
    ### 權限
    - Public
    """
    return await service.institute.read(institute_id)


class EditInstituteInput(BaseModel):
    abbreviated_name: str = None
    full_name: str = None
    email_domain: str = None
    is_disabled: bool = None


@router.patch('/institute/{institute_id}')
@enveloped
async def edit_institute(institute_id: int, data: EditInstituteInput, request: Request) -> None:
    """
    ### 權限
    - System Manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await service.institute.edit(
        institute_id=institute_id,
        abbreviated_name=data.abbreviated_name,
        full_name=data.full_name,
        email_domain=data.email_domain,
        is_disabled=data.is_disabled,
    )
