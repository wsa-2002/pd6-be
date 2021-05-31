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
    tags=['Testdata'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/testdata/{testdata_id}')
@util.enveloped
def read_testdata(testdata_id: int):
    if testdata_id is 1:
        return model.testdata_1
    elif testdata_id is 2:
        return model.testdata_2
    else:
        raise Exception


@router.patch('/testdata/{testdata_id}')
@util.enveloped
def edit_testdata(testdata_id: int):
    pass


@router.delete('/testdata/{testdata_id}')
@util.enveloped
def delete_testdata(testdata_id: int):
    pass
