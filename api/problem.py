from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Problem'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/problem')
async def browse_problem() -> Sequence[do.Problem]:
    return await db.problem.browse()


@router.get('/problem/{problem_id}')
async def read_problem(problem_id: int):
    return await db.problem.read(problem_id=problem_id)


class EditProblemInput(BaseModel):
    title: str = None
    full_score: int = None
    description: Optional[str] = ...
    source: Optional[str] = ...
    hint: Optional[str] = ...
    is_hidden: bool = None


@router.patch('/problem/{problem_id}')
async def edit_problem(problem_id: int, data: EditProblemInput, request: auth.Request):
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await db.problem.read(problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await db.problem.edit(problem_id, title=data.title, full_score=data.full_score,
                                 description=data.description, source=data.source,
                                 hint=data.hint, is_hidden=data.is_hidden)


@router.delete('/problem/{problem_id}')
async def delete_problem(problem_id: int, request: auth.Request):
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await db.problem.read(problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await db.problem.delete(problem_id=problem_id)


class AddTestcaseInput(BaseModel):
    is_sample: bool
    score: int
    time_limit: int
    memory_limit: int
    is_disabled: bool


@router.post('/problem/{problem_id}/testcase', tags=['Testcase'])
async def add_testcase_under_problem(problem_id: int, data: AddTestcaseInput, request: auth.Request) -> int:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await db.problem.read(problem_id, include_hidden=True)
    challenge = await db.challenge.read(problem.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await db.testcase.add(problem_id=problem_id, is_sample=data.is_sample, score=data.score,
                                 input_file=None, output_file=None,
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


async def browse_testcase_under_problem(problem_id: int, request: auth.Request) -> Sequence[ReadTestcaseOutput]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    testcases = await db.testcase.browse(problem_id=problem_id)
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
