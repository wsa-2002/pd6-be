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
    tags=['Testcase'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/testcase/{testcase_id}')
async def read_testcase(testcase_id: int) -> do.Testcase:
    return await db.testcase.read(testcase_id=testcase_id)


class EditTestcaseInput(BaseModel):
    is_sample: bool
    score: int
    input_file: str  # TODO
    output_file: str  # TODO
    time_limit: int
    memory_limit: int
    is_enabled: bool
    is_hidden: bool


@router.patch('/testcase/{testcase_id}')
async def edit_testcase(testcase_id: int, data: EditTestcaseInput) -> None:
    await db.testcase.edit(testcase_id=testcase_id, is_sample=data.is_sample, score=data.score,
                           input_file=data.input_file, output_file=data.output_file,
                           time_limit=data.time_limit, memory_limit=data.memory_limit,
                           is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.delete('/testcase/{testcase_id}')
async def delete_testcase(testcase_id: int) -> None:
    await db.testcase.delete(testcase_id=testcase_id)
