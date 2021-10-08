from fastapi import File, UploadFile
from pydantic import BaseModel

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .problem import ReadTestcaseOutput
from .util import rbac, file

router = APIRouter(
    tags=['Testcase'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/testcase/{testcase_id}')
@enveloped
async def read_testcase(testcase_id: int, request: Request) -> ReadTestcaseOutput:
    """
    ### 權限
    - System normal
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await service.testcase.read(testcase_id=testcase_id)
    problem = await service.problem.read(testcase.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)

    return ReadTestcaseOutput(
        id=testcase.id,
        problem_id=testcase.problem_id,
        is_sample=testcase.is_sample,
        score=testcase.score,
        input_file_uuid=testcase.input_file_uuid if (testcase.is_sample or is_class_manager) else None,
        output_file_uuid=testcase.output_file_uuid if (testcase.is_sample or is_class_manager) else None,
        input_filename=testcase.input_filename,
        output_filename=testcase.output_filename,
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


@router.patch('/testcase/{testcase_id}')
@enveloped
async def edit_testcase(testcase_id: int, data: EditTestcaseInput, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await service.testcase.read(testcase_id)
    problem = await service.problem.read(testcase.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await service.testcase.edit(testcase_id=testcase_id, is_sample=data.is_sample, score=data.score,
                                time_limit=data.time_limit, memory_limit=data.memory_limit,
                                is_disabled=data.is_disabled)


@router.put('/testcase/{testcase_id}/input-data')
@enveloped
async def upload_testcase_input_data(testcase_id: int, request: Request, input_file: UploadFile = File(...)) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await service.testcase.read(testcase_id)
    problem = await service.problem.read(testcase.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    # Issue #26: CRLF
    no_cr_file = file.replace_cr(input_file.file.read())

    await service.testcase.edit_input(testcase_id=testcase.id, file=no_cr_file, filename=input_file.filename)


@router.put('/testcase/{testcase_id}/output-data')
@enveloped
async def upload_testcase_output_data(testcase_id: int, request: Request, output_file: UploadFile = File(...)):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await service.testcase.read(testcase_id)
    problem = await service.problem.read(testcase.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    # Issue #26: CRLF
    no_cr_file = file.replace_cr(output_file.file.read())

    await service.testcase.edit_output(testcase_id=testcase.id, file=no_cr_file, filename=output_file.filename)


@router.delete('/testcase/{testcase_id}')
@enveloped
async def delete_testcase(testcase_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await service.testcase.read(testcase_id)
    problem = await service.problem.read(testcase.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await service.testcase.delete(testcase_id=testcase_id)


@router.delete('/testcase/{testcase_id}/input-data')
@enveloped
async def delete_testcase_input_data(testcase_id: int, request: Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await service.testcase.read(testcase_id)
    problem = await service.problem.read(testcase.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await service.testcase.delete_input_data(testcase_id=testcase_id)


@router.delete('/testcase/{testcase_id}/output-data')
@enveloped
async def delete_testcase_output_data(testcase_id: int, request: Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    testcase = await service.testcase.read(testcase_id)
    problem = await service.problem.read(testcase.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await service.testcase.delete_output_data(testcase_id=testcase_id)
