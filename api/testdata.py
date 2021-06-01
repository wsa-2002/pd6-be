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
    tags=['Testdata'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/testdata/{testdata_id}')
def read_testdata(testdata_id: int) -> do.Testdata:
    return await db.testdata.read(testdata_id=testdata_id)


class EditTestdataInput(BaseModel):
    is_sample: bool
    score: int
    input_file: str  # TODO
    output_file: str  # TODO
    time_limit: int
    memory_limit: int
    is_enabled: bool
    is_hidden: bool


@router.patch('/testdata/{testdata_id}')
def edit_testdata(testdata_id: int, data: EditTestdataInput) -> None:
    await db.testdata.edit(testdata_id=testdata_id, is_sample=data.is_sample, score=data.score,
                           input_file=data.input_file, output_file=data.output_file,
                           time_limit=data.time_limit, memory_limit=data.memory_limit,
                           is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.delete('/testdata/{testdata_id}')
def delete_testdata(testdata_id: int) -> None:
    await db.testdata.delete(testdata_id=testdata_id)
