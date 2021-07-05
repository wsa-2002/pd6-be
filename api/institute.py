from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Institute'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


class AddInstituteInput(BaseModel):
    name: str
    email_domain: str
    is_disabled: bool


@dataclass
class AddInstituteOutput:
    id: int


@router.post('/institute')
@enveloped
async def add_institute(data: AddInstituteInput, request: auth.Request) -> AddInstituteOutput:
    """
    ### 權限
    - System Manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    institute_id = await db.institute.add(name=data.name, email_domain=data.email_domain, is_disabled=data.is_disabled)
    return AddInstituteOutput(id=institute_id)


@router.get('/institute', tags=['Public'])
@enveloped
async def browse_institute() -> Sequence[do.Institute]:
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
    name: str = None
    email_domain: str = None
    is_disabled: bool = None


@router.patch('/institute/{institute_id}')
@enveloped
async def edit_institute(institute_id: int, data: EditInstituteInput, request: auth.Request) -> None:
    """
    ### 權限
    - System Manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.institute.edit(
        institute_id=institute_id,
        name=data.name,
        email_domain=data.email_domain,
        is_disabled=data.is_disabled,
    )
