from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do, enum
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Task'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/task/{task_id}')
async def read_task(task_id: int, request: auth.Request) -> do.Task:
    return await db.task.read(task_id=task_id)


class EditTaskInput(BaseModel):
    identifier: str
    selection_type: enum.TaskSelectionType
    is_hidden: bool = None


@router.patch('/task/{task_id}')
async def edit_task(task_id: int, data: EditTaskInput, request: auth.Request) -> None:
    await db.task.edit(
        task_id=task_id,
        identifier=data.identifier,
        selection_type=data.selection_type,
        is_hidden=data.is_hidden,
    )


@router.delete('/task/{task_id}')
async def delete_task(task_id: int, request: auth.Request) -> None:
    await db.task.delete(task_id)
