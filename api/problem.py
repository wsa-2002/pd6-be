from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do, enum
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
def browse_problems() -> Sequence[do.Problem]:
    return await db.problem.browse()


@router.get('/problem/{problem_id}')
def read_problem(problem_id: int):
    return await db.problem.read(problem_id=problem_id)


class EditProblemInput(BaseModel):
    type: enum.ProblemType
    name: str
    full_score: int
    description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_enabled: bool
    is_hidden: bool


@router.patch('/problem/{problem_id}')
def edit_problem(problem_id: int):
    pass


@router.delete('/problem/{problem_id}')
def delete_problem(problem_id: int):
    return await db.problem.delete(problem_id=problem_id)


class AddTestcaseInput(BaseModel):
    is_sample: bool
    score: int
    input_file: str  # TODO
    output_file: str  # TODO
    time_limit: int
    memory_limit: int
    is_enabled: bool
    is_hidden: bool


@router.post('/problem/{problem_id}/testcase', tags=['Testcase'])
def add_testcase_under_problem(problem_id: int, data: AddTestcaseInput) -> int:
    return await db.problem.add_testcase(problem_id=problem_id, is_sample=data.is_sample, score=data.score,
                                         input_file=data.input_file, output_file=data.output_file,
                                         time_limit=data.time_limit, memory_limit=data.memory_limit,
                                         is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.get('/problem/{problem_id}/testcase', tags=['Testcase'])
def browse_testcase_under_problem(problem_id: int) -> Sequence[do.Testcase]:
    return await db.problem.browse_testcases(problem_id=problem_id)
