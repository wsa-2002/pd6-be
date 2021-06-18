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
    tags=['Challenge'],
    default_response_class=envelope.JSONResponse,
)


class AddChallengeInput(BaseModel):
    class_id: int
    type: enum.ChallengeType
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_hidden: bool


@router.post('/class/{class_id}/challenge', tags=['Course'])
async def add_challenge_under_class(class_id: int, data: AddChallengeInput, request: auth.Request) -> int:
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    challenge_id = await db.challenge.add(
        class_id=class_id, type_=data.type, title=data.title, setter_id=request.account.id,
        description=data.description, start_time=data.start_time, end_time=data.end_time, is_hidden=data.is_hidden,
    )
    return challenge_id


@router.get('/class/{class_id}/challenge', tags=['Course'])
async def browse_challenge_under_class(class_id: int, request: auth.Request) -> Sequence[do.Challenge]:
    class_role = await rbac.get_role(request.account.id, class_id=class_id)

    if class_role < RoleType.guest:
        raise exc.NoPermission

    return await db.challenge.browse(class_id=class_id, include_hidden=class_role >= RoleType.manager)


@router.get('/challenge')
async def browse_challenge(request: auth.Request) -> Sequence[do.Challenge]:
    # TODO: 這要怎麼做啊？ (權限)
    #       甚至有這個 api 的需求嗎？ XD

    challenges = await db.challenge.browse()
    return challenges


@router.get('/challenge/{challenge_id}')
async def read_challenge(challenge_id: int, request: auth.Request) -> do.Challenge:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    if (challenge.is_hidden and class_role < RoleType.manager
            or class_role < RoleType.normal):
        raise exc.NoPermission

    return challenge


class EditChallengeInput(BaseModel):
    # class_id: int
    type: enum.ChallengeType = None
    title: str = None
    description: Optional[str] = ...
    start_time: datetime = None
    end_time: datetime = None
    is_hidden: bool = None


@router.patch('/challenge/{challenge_id}')
async def edit_challenge(challenge_id: int, data: EditChallengeInput, request: auth.Request) -> None:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.challenge.edit(challenge_id=challenge_id, type_=data.type, title=data.title,
                            description=data.description, start_time=data.start_time, end_time=data.end_time,
                            is_hidden=data.is_hidden)


@router.delete('/challenge/{challenge_id}')
async def delete_challenge(challenge_id: int, request: auth.Request) -> None:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.challenge.delete(challenge_id)


class AddTaskInput(BaseModel):
    identifier: str
    selection_type: enum.TaskSelectionType
    problem_id: Optional[int] = ...
    peer_review_id: Optional[int] = ...
    is_hidden: bool


@router.post('/challenge/{challenge_id}/task', tags=['Task'])
async def add_task_under_challenge(challenge_id: int, data: AddTaskInput, request: auth.Request) -> int:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await db.task.add(challenge_id=challenge_id, identifier=data.identifier, selection_type=data.selection_type,
                             problem_id=data.problem_id, peer_review_id=data.peer_review_id, is_hidden=data.is_hidden)


@router.get('/challenge/{challenge_id}/task', tags=['Task'])
async def browse_task_under_challenge(challenge_id: int, request: auth.Request) -> Sequence[do.Task]:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    if class_role < RoleType.guest:
        raise exc.NoPermission

    return await db.task.browse(challenge_id=challenge_id, include_hidden=class_role >= RoleType.manager)
