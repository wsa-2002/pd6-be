from pydantic import BaseModel

from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac

from .problem import ReadTestcaseOutput


router = APIRouter(
    tags=['Testcase'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/testcase/{testcase_id}')
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
async def read_testcase_input_data(testcase_id: int, request: auth.Request):
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

    testcase = await db.testcase.read(testcase_id)
    ...  # TODO


@router.get('/testcase/{testcase_id}/output-data')
async def read_testcase_output_data(testcase_id: int, request: auth.Request):
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

    testcase = await db.testcase.read(testcase_id)
    ...  # TODO


@router.patch('/testcase/{testcase_id}')
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
async def edit_testcase_input_data(testcase_id: int, request: auth.Request):
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

    await db.testcase.read(testcase_id, include_deleted=False)  # Make sure it's there
    ...  # TODO


@router.put('/testcase/{testcase_id}/output-data')
async def edit_testcase_output_data(testcase_id: int, request: auth.Request):
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

    await db.testcase.read(testcase_id, include_deleted=False)  # Make sure it's there
    ...  # TODO


@router.delete('/testcase/{testcase_id}')
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

    await db.testcase.read(testcase_id, include_deleted=False)  # Make sure it's there
    ...  # TODO


@router.delete('/testcase/{testcase_id}/output-data')
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

    await db.testcase.read(testcase_id, include_deleted=False)  # Make sure it's there
    ...  # TODO
