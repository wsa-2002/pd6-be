from dataclasses import dataclass
from uuid import UUID

from fastapi import UploadFile, File

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
from persistence import s3

from .util import rbac, file

router = APIRouter(
    tags=['Assisting Data'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class ReadAssistingDataOutput:
    id: int
    problem_id: int
    s3_file_uuid: UUID
    filename: str


@router.get('/assisting-data/{assisting_data_id}')
@enveloped
async def read_assisting_data(assisting_data_id: int, request: Request) -> ReadAssistingDataOutput:
    """
    ### 權限
    - class manager
    """
    assisting_data = await db.assisting_data.read(assisting_data_id=assisting_data_id)
    problem = await db.problem.read(assisting_data.problem_id)
    challenge = await db.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return ReadAssistingDataOutput(id=assisting_data.id,
                                   problem_id=assisting_data.problem_id,
                                   s3_file_uuid=assisting_data.s3_file_uuid,
                                   filename=assisting_data.filename)


@router.put('/assisting-data/{assisting_data_id}')
@enveloped
async def edit_assisting_data(assisting_data_id: int, request: Request, assisting_data_file: UploadFile = File(...)) \
        -> None:
    """
    ### 權限
    - class manager
    """
    assisting_data = await db.assisting_data.read(assisting_data_id=assisting_data_id)
    problem = await db.problem.read(assisting_data.problem_id)
    challenge = await db.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    # Issue #26: CRLF
    no_cr_file = file.replace_cr(assisting_data_file.file)

    s3_file = await s3.assisting_data.upload(no_cr_file)

    s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    await db.assisting_data.edit(assisting_data_id=assisting_data_id, s3_file_uuid=s3_file_uuid,
                                 filename=assisting_data_file.filename)


@router.delete('/assisting-data/{assisting_data_id}')
@enveloped
async def delete_assisting_data(assisting_data_id: int, request: Request) -> None:
    """
    ### 權限
    - class manager
    """
    assisting_data = await db.assisting_data.read(assisting_data_id=assisting_data_id)
    problem = await db.problem.read(assisting_data.problem_id)
    challenge = await db.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.assisting_data.delete(assisting_data_id=assisting_data.id)
