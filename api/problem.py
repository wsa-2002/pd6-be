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


@router.post('/problem/{problem_id}/testdata', tags=['Testdata'])
@util.enveloped
def add_testdata_under_problem(problem_id: int):
    return {'id': 1}


@router.get('/problem/{problem_id}/testdata', tags=['Testdata'])
@util.enveloped
def browse_testdata_under_problem(problem_id: int):
    return [model.testdata_1, model.testdata_2]

