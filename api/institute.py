from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db


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
