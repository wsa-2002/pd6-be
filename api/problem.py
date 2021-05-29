from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel

from base import enum
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
@util.enveloped
def get_problems():
    return [model.problem]


@router.get('/problem/{problem_id}')
@util.enveloped
def get_problem(problem_id: int):
    return model.problem


@router.patch('/problem/{problem_id}')
@util.enveloped
def modify_problem(problem_id: int):
    pass


@router.delete('/problem/{problem_id}')
@util.enveloped
def remove_problem(problem_id: int):
    pass


@router.post('/problem/{problem_id}/testdata')
@util.enveloped
def create_testdata_under_problem(problem_id: int):
    return {'id': 1}


@router.get('/problem/{problem_id}/testdata')
@util.enveloped
def get_testdata_under_problem(problem_id: int):
    return [model.testdata_1, model.testdata_2]


@router.get('/testdata/{testdata_id}')
@util.enveloped
def get_testdata(testdata_id: int):
    if testdata_id is 1:
        return model.testdata_1
    elif testdata_id is 2:
        return model.testdata_2
    else:
        raise Exception


@router.patch('/testdata/{testdata_id}')
@util.enveloped
def modify_testdata(testdata_id: int):
    pass


@router.delete('/testdata/{testdata_id}')
@util.enveloped
def remove_testdata(testdata_id: int):
    pass
