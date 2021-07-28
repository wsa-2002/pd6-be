from pydantic import BaseModel

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import persistence.s3 as s3
from util import rbac
from fastapi import UploadFile, File
from .problem import ReadTestcaseOutput
from config import s3_config


router = APIRouter(
    tags=['Testcase'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


@router.get('/testcase/{testcase_id}')
@enveloped
async def read_testcase(testcase_id: int, request: auth.Request) -> ReadTestcaseOutput:
    """
    ### 權限
    - System normal
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    testcase = await db.testcase.read(testcase_id=testcase_id)
    return ReadTestcaseOutput(
        id=testcase.id,
        problem_id=testcase.problem_id,
        is_sample=testcase.is_sample,
        score=testcase.score,
        time_limit=testcase.time_limit,
        memory_limit=testcase.memory_limit,
        is_disabled=testcase.is_disabled,
        is_deleted=testcase.is_deleted,
    )


class EditTestcaseInput(BaseModel):
    is_sample: bool = None
    score: int = None
    time_limit: int = None
    memory_limit: int = None
    is_disabled: bool = None


@router.get('/testcase/{testcase_id}/input-data')
@enveloped
async def download_testcase_input_data(testcase_id: int, request: auth.Request) -> str:
    """
    ### 權限
    - System Normal(Sample)
    - Class Manager(All)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await (rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)
                  or (testcase.is_sample and rbac.validate(request.account.id, RoleType.normal))):
        raise exc.NoPermission

    input_file = await db.s3_file.read(s3_file_id=testcase.input_file_id)
    url = f'{s3_config.endpoint}/{input_file.bucket}/{input_file.key}'
    return url


@router.get('/testcase/{testcase_id}/output-data')
@enveloped
async def download_testcase_output_data(testcase_id: int, request: auth.Request) -> str:
    """
    ### 權限
    - System Normal(Sample)
    - Class Manager(All)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await (rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)
                  or (testcase.is_sample and rbac.validate(request.account.id, RoleType.normal))):
        raise exc.NoPermission

    output_file = await db.s3_file.read(s3_file_id=testcase.output_file_id)
    url = f'{s3_config.endpoint}/{output_file.bucket}/{output_file.key}'
    return url


@router.patch('/testcase/{testcase_id}')
@enveloped
async def edit_testcase(testcase_id: int, data: EditTestcaseInput, request: auth.Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.testcase.edit(testcase_id=testcase_id, is_sample=data.is_sample, score=data.score,
                           time_limit=data.time_limit, memory_limit=data.memory_limit,
                           is_disabled=data.is_disabled)


@router.put('/testcase/{testcase_id}/input-data')
@enveloped
async def upload_testcase_input_data(testcase_id: int, request: auth.Request, input_file: UploadFile = File(...)):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    # 流程: 先upload到s3取得bucket, key
    #       bucket, key進s3_file db得到file id
    #       file_id進testcase db
    bucket, key = await s3.testcase.upload_input(file=input_file.file,
                                                 filename=input_file.filename,
                                                 testcase_id=testcase_id)

    file_id = await db.s3_file.add(bucket=bucket, key=key)
    await db.testcase.edit(testcase_id=testcase_id, input_file_id=file_id)


@router.put('/testcase/{testcase_id}/output-data')
@enveloped
async def upload_testcase_output_data(testcase_id: int, request: auth.Request, output_file: UploadFile = File(...)):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    # 流程: 先upload到s3取得bucket, key
    #       bucket, key進s3_file db得到file id
    #       file_id進testcase db
    bucket, key = await s3.testcase.upload_output(file=output_file.file,
                                                  filename=output_file.filename,
                                                  testcase_id=testcase_id)
    file_id = await db.s3_file.add(bucket=bucket, key=key)
    await db.testcase.edit(testcase_id=testcase_id, output_file_id=file_id)


@router.delete('/testcase/{testcase_id}')
@enveloped
async def delete_testcase(testcase_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.testcase.delete(testcase_id=testcase_id)


@router.delete('/testcase/{testcase_id}/input-data')
@enveloped
async def delete_testcase_input_data(testcase_id: int, request: auth.Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.testcase.delete_input_data(testcase_id=testcase_id)


@router.delete('/testcase/{testcase_id}/output-data')
@enveloped
async def delete_testcase_output_data(testcase_id: int, request: auth.Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await db.testcase.read(testcase_id)
    problem = await db.problem.read(testcase.problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.testcase.delete_output_data(testcase_id=testcase_id)
