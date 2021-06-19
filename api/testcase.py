from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

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
async def read_testcase(testcase_id: int, request: auth.Request) -> do.Testcase:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # TODO: normal should not see input and output (maybe use another solution)
    return await db.testcase.read(testcase_id=testcase_id)


class EditTestcaseInput(BaseModel):
    is_sample: bool = None
    score: int = None
    input_file: str = None  # TODO
    output_file: str = None  # TODO
    time_limit: int = None
    memory_limit: int = None
    is_disabled: bool = None


@router.patch('/testcase/{testcase_id}')
async def edit_testcase(testcase_id: int, data: EditTestcaseInput, request: auth.Request) -> None:
    # 因為需要 problem_id 才能判斷權限，所以先 read
    testcase = await db.testcase.read(testcase_id)
    related_classes = await db.class_.browse_from_problem(problem_id=testcase.problem_id, include_hidden=True)
    # 只要 account 在任何一個 class 是 manager 就 ok
    if not any(await rbac.validate(request.account.id, RoleType.manager, class_id=related_class.id)
               for related_class in related_classes):
        raise exc.NoPermission

    await db.testcase.edit(testcase_id=testcase_id, is_sample=data.is_sample, score=data.score,
                           input_file=data.input_file, output_file=data.output_file,
                           time_limit=data.time_limit, memory_limit=data.memory_limit,
                           is_disabled=data.is_disabled)


@router.delete('/testcase/{testcase_id}')
async def delete_testcase(testcase_id: int, request: auth.Request) -> None:
    # 因為需要 problem_id 才能判斷權限，所以先 read
    testcase = await db.testcase.read(testcase_id)
    related_classes = await db.class_.browse_from_problem(problem_id=testcase.problem_id, include_hidden=True)
    # 只要 account 在任何一個 class 是 manager 就 ok
    if not any(await rbac.validate(request.account.id, RoleType.manager, class_id=related_class.id)
               for related_class in related_classes):
        raise exc.NoPermission

    await db.testcase.delete(testcase_id=testcase_id)
