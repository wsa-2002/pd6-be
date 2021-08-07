from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType, ChallengePublicizeType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
from .util import rbac

from .. import service


router = APIRouter(
    tags=['Problem'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/problem')
@enveloped
async def browse_problem_set(request: Request) -> Sequence[do.Problem]:
    """
    ### 權限
    - System normal (not hidden)
    """
    system_role = await rbac.get_role(request.account.id)
    if not system_role >= RoleType.normal:
        raise exc.NoPermission

    return await service.problem.browse_problem_set(request_time=request.time)


@router.get('/problem/{problem_id}')
@enveloped
async def read_problem(problem_id: int, request: Request) -> do.Problem:
    """
    ### 權限
    - Class manager (hidden)
    - System normal (not hidden)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    is_system_normal = await rbac.validate(request.account.id, RoleType.normal)
    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = request.time >= publicize_time

    if not (is_class_manager or (is_system_normal and is_challenge_publicized)):
        raise exc.NoPermission

    return problem


class EditProblemInput(BaseModel):
    title: str = None
    full_score: int = None
    description: Optional[str] = ...
    source: Optional[str] = ...
    hint: Optional[str] = ...


@router.patch('/problem/{problem_id}')
@enveloped
async def edit_problem(problem_id: int, data: EditProblemInput, request: Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await service.problem.edit(problem_id, title=data.title, full_score=data.full_score,
                                      description=data.description, source=data.source,
                                      hint=data.hint)


@router.delete('/problem/{problem_id}')
@enveloped
async def delete_problem(problem_id: int, request: Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await service.problem.delete(problem_id=problem_id)


class AddTestcaseInput(BaseModel):
    is_sample: bool
    score: int
    time_limit: int
    memory_limit: int
    is_disabled: bool


@router.post('/problem/{problem_id}/testcase', tags=['Testcase'])
@enveloped
async def add_testcase_under_problem(problem_id: int, data: AddTestcaseInput, request: Request) -> int:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await service.testcase.add(problem_id=problem_id, is_sample=data.is_sample, score=data.score,
                                      input_file_id=None, output_file_id=None,
                                      time_limit=data.time_limit, memory_limit=data.memory_limit,
                                      is_disabled=data.is_disabled)


@dataclass
class ReadTestcaseOutput:
    id: int
    problem_id: int
    is_sample: bool
    score: int
    time_limit: int
    memory_limit: int
    is_disabled: bool
    is_deleted: bool


async def browse_testcase_under_problem(problem_id: int, request: Request) -> Sequence[ReadTestcaseOutput]:
    """
    ### 權限
    - System normal
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    testcases = await service.testcase.browse(problem_id=problem_id)
    return [ReadTestcaseOutput(
        id=testcase.id,
        problem_id=testcase.problem_id,
        is_sample=testcase.is_sample,
        score=testcase.score,
        time_limit=testcase.time_limit,
        memory_limit=testcase.memory_limit,
        is_disabled=testcase.is_disabled,
        is_deleted=testcase.is_deleted,
    ) for testcase in testcases]