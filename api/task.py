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
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    task = await db.task.read(task_id=task_id)
    challenge = await db.challenge.read(challenge_id=task.challenge_id)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    if class_role < RoleType.guest or task.is_hidden and class_role < RoleType.manager:
        raise exc.NoPermission

    return task


class EditTaskInput(BaseModel):
    identifier: str = None
    selection_type: enum.TaskSelectionType = None
    is_hidden: bool = None


@router.patch('/task/{task_id}')
async def edit_task(task_id: int, data: EditTaskInput, request: auth.Request) -> None:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    task = await db.task.read(task_id=task_id)
    challenge = await db.challenge.read(challenge_id=task.challenge_id)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.task.edit(
        task_id=task_id,
        identifier=data.identifier,
        selection_type=data.selection_type,
        is_hidden=data.is_hidden,
    )


@router.delete('/task/{task_id}')
async def delete_task(task_id: int, request: auth.Request) -> None:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    task = await db.task.read(task_id=task_id)
    challenge = await db.challenge.read(challenge_id=task.challenge_id)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.task.delete(task_id)
