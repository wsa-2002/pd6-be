from dataclasses import dataclass
from typing import Optional, Sequence

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


@dataclass
class AddInstituteOutput:
    id: int


@router.post('/institute')
async def add_institute(data: AddInstituteInput, request: auth.Request) -> AddInstituteOutput:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    institute_id = await db.institute.add(name=data.name, email_domain=data.email_domain)
    return AddInstituteOutput(id=institute_id)


@router.get('/institute', tags=['Public'])
async def browse_institute(request: auth.Request) -> Sequence[do.Institute]:
    try:
        only_enabled = request.account.role.not_manager
    except exc.NoPermission:
        only_enabled = True

    return await db.institute.browse(only_enabled=only_enabled)


@router.get('/institute/{institute_id}')
async def read_institute(institute_id: int, request: auth.Request) -> do.Institute:
    return await db.institute.read(institute_id, only_enabled=request.account.role.not_manager)


class EditInstituteInput(BaseModel):
    name: Optional[str]
    email_domain: Optional[str]
    is_enabled: Optional[bool]


@router.patch('/institute/{institute_id}')
async def edit_institute(institute_id: int, data: EditInstituteInput, request: auth.Request) -> None:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    await db.institute.edit(
        institute_id=institute_id,
        name=data.name,
        email_domain=data.email_domain,
        is_enabled=data.is_enabled,
    )
