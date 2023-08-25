from fastapi import File, UploadFile
from pydantic import BaseModel, PositiveInt
from typing import Optional

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from persistence import s3
import util
from util import model
from util.context import context

from .problem import ReadTestcaseOutput

router = APIRouter(
    tags=['Testcase'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/testcase/{testcase_id}')
@enveloped
async def read_testcase(testcase_id: int) -> ReadTestcaseOutput:
    """
    ### 權限
    - System normal
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    class_role = await service.rbac.get_class_role(context.account.id, testcase_id=testcase_id)
    is_class_manager = class_role >= RoleType.manager

    testcase = await db.testcase.read(testcase_id=testcase_id)
    return ReadTestcaseOutput(
        id=testcase.id,
        problem_id=testcase.problem_id,
        is_sample=testcase.is_sample,
        score=testcase.score,
        label=testcase.label,
        input_file_uuid=testcase.input_file_uuid if (testcase.is_sample or is_class_manager) else None,
        output_file_uuid=testcase.output_file_uuid if (testcase.is_sample or is_class_manager) else None,
        input_filename=testcase.input_filename,
        output_filename=testcase.output_filename,
        note=testcase.note,
        time_limit=testcase.time_limit,
        memory_limit=testcase.memory_limit,
        is_disabled=testcase.is_disabled,
        is_deleted=testcase.is_deleted,
    )


class EditTestcaseInput(BaseModel):
    is_sample: bool = None
    score: int = None
    time_limit: PositiveInt = None
    memory_limit: PositiveInt = None
    note: Optional[str] = model.can_omit
    is_disabled: bool = None
    label: str = None


@router.patch('/testcase/{testcase_id}')
@enveloped
async def edit_testcase(testcase_id: int, data: EditTestcaseInput) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, testcase_id=testcase_id):
        raise exc.NoPermission

    await db.testcase.edit(testcase_id=testcase_id, is_sample=data.is_sample, score=data.score, label=data.label,
                           time_limit=data.time_limit, memory_limit=data.memory_limit,
                           is_disabled=data.is_disabled, note=data.note)


@router.put('/testcase/{testcase_id}/input-data')
@enveloped
async def upload_testcase_input_data(testcase_id: int, input_file: UploadFile = File(...)) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, testcase_id=testcase_id):
        raise exc.NoPermission

    # Issue #26: CRLF
    no_cr_file = util.file.replace_cr(input_file.file)

    # 流程: 先 upload 到 s3 取得 bucket, key
    #       bucket, key 進 s3_file db 得到 file id
    #       file_id 進 testcase db
    s3_file = await s3.testdata.upload(no_cr_file)
    file_id = await db.s3_file.add_with_do(s3_file=s3_file)
    await db.testcase.edit(testcase_id=testcase_id, input_file_uuid=file_id, input_filename=input_file.filename)


@router.put('/testcase/{testcase_id}/output-data')
@enveloped
async def upload_testcase_output_data(testcase_id: int, output_file: UploadFile = File(...)):
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, testcase_id=testcase_id):
        raise exc.NoPermission

    # Issue #26: CRLF
    no_cr_file = util.file.replace_cr(output_file.file)

    # 流程: 先 upload 到 s3 取得 bucket, key
    #       bucket, key 進 s3_file db 得到 file id
    #       file_id 進 testcase db
    s3_file = await s3.testdata.upload(no_cr_file)
    file_id = await db.s3_file.add_with_do(s3_file=s3_file)
    await db.testcase.edit(testcase_id=testcase_id, output_file_uuid=file_id, output_filename=output_file.filename)


@router.delete('/testcase/{testcase_id}')
@enveloped
async def delete_testcase(testcase_id: int) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, testcase_id=testcase_id):
        raise exc.NoPermission

    await db.testcase.delete(testcase_id=testcase_id)


@router.delete('/testcase/{testcase_id}/input-data')
@enveloped
async def delete_testcase_input_data(testcase_id: int):
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, testcase_id=testcase_id):
        raise exc.NoPermission

    await db.testcase.delete_input_data(testcase_id=testcase_id)


@router.delete('/testcase/{testcase_id}/output-data')
@enveloped
async def delete_testcase_output_data(testcase_id: int):
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, testcase_id=testcase_id):
        raise exc.NoPermission

    await db.testcase.delete_output_data(testcase_id=testcase_id)
