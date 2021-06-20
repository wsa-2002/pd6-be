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
    tags=['Institute'],
    default_response_class=envelope.JSONResponse,
)


class AddInstituteInput(BaseModel):
    name: str
    email_domain: str
    is_disabled: bool


@dataclass
class AddInstituteOutput:
    id: int


@router.post('/institute')
async def add_institute(data: AddInstituteInput, request: auth.Request) -> AddInstituteOutput:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    institute_id = await db.institute.add(name=data.name, email_domain=data.email_domain, is_disabled=data.is_disabled)
    return AddInstituteOutput(id=institute_id)


@router.get('/institute', tags=['Public'])
async def browse_institute() -> Sequence[do.Institute]:
    return await db.institute.browse()


@router.get('/institute/{institute_id}', tags=['Public'])
async def read_institute(institute_id: int) -> do.Institute:
    return await db.institute.read(institute_id)


class EditInstituteInput(BaseModel):
    name: str = None
    email_domain: str = None
    is_disabled: bool = None


@router.patch('/institute/{institute_id}')
async def edit_institute(institute_id: int, data: EditInstituteInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.institute.edit(
        institute_id=institute_id,
        name=data.name,
        email_domain=data.email_domain,
        is_disabled=data.is_disabled,
    )
