from dataclasses import dataclass
from uuid import UUID

from fastapi import UploadFile, File

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from persistence import s3
import service
import util
from util.context import context

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
async def read_assisting_data(assisting_data_id: int) -> ReadAssistingDataOutput:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, assisting_data_id=assisting_data_id):
        raise exc.NoPermission

    assisting_data = await db.assisting_data.read(assisting_data_id=assisting_data_id)
    return ReadAssistingDataOutput(id=assisting_data.id,
                                   problem_id=assisting_data.problem_id,
                                   s3_file_uuid=assisting_data.s3_file_uuid,
                                   filename=assisting_data.filename)


@router.put('/assisting-data/{assisting_data_id}')
@enveloped
async def edit_assisting_data(assisting_data_id: int, assisting_data_file: UploadFile = File(...)) \
        -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, assisting_data_id=assisting_data_id):
        raise exc.NoPermission

    # Issue #26: CRLF
    no_cr_file = util.file.replace_cr(assisting_data_file.file)

    s3_file = await s3.assisting_data.upload(no_cr_file)

    s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    await db.assisting_data.edit(assisting_data_id=assisting_data_id, s3_file_uuid=s3_file_uuid,
                                 filename=assisting_data_file.filename)


@router.delete('/assisting-data/{assisting_data_id}')
@enveloped
async def delete_assisting_data(assisting_data_id: int) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, assisting_data_id=assisting_data_id):
        raise exc.NoPermission

    await db.assisting_data.delete(assisting_data_id=assisting_data_id)
