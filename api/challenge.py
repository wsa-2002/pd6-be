from datetime import datetime
from typing import Optional, Sequence, Collection, List

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
    is_enabled: bool
    is_hidden: bool


@router.post('/class/{class_id}/challenge', tags=['Course'])
async def add_challenge_under_class(class_id: int, data: AddChallengeInput, request: auth.Request) -> int:
    if not (await rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False)
            or await rbac.validate(request.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    challenge_id = await db.challenge.add(
        class_id=class_id, type_=data.type, title=data.title, setter_id=request.account.id, description=data.description,
        start_time=data.start_time, end_time=data.end_time, is_enabled=data.is_enabled, is_hidden=data.is_hidden,
    )
    return challenge_id


@router.get('/class/{class_id}/challenge', tags=['Course'])
async def browse_challenge_under_class(class_id: int, request: auth.Request) -> Sequence[do.Challenge]:
    if not rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False):
        raise exc.NoPermission

    challenges = await db.challenge.browse(class_id=class_id)
    return challenges


@router.get('/challenge')
async def browse_challenge(request: auth.Request) -> Sequence[do.Challenge]:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    challenges = await db.challenge.browse()
    return challenges


@router.get('/challenge/{challenge_id}')
async def read_challenge(challenge_id: int, request: auth.Request) -> do.Challenge:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    challenge = await db.challenge.read(challenge_id=challenge_id)
    return challenge


class EditChallengeInput(BaseModel):
    # class_id: int
    type: Optional[enum.ChallengeType]
    title: Optional[str]
    description: Optional[str] = ...
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_enabled: Optional[bool]
    is_hidden: Optional[bool]


@router.patch('/challenge/{challenge_id}')
async def edit_challenge(challenge_id: int, data: EditChallengeInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    await db.challenge.edit(challenge_id=challenge_id, type_=data.type, title=data.title,
                            description=data.description, start_time=data.start_time, end_time=data.end_time,
                            is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.delete('/challenge/{challenge_id}')
async def delete_challenge(challenge_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    # TODO


class AddTaskInput(BaseModel):
    identifier: str
    selection_type: enum.TaskSelectionType
    problem_id: Optional[int] = None
    peer_review_id: Optional[int] = None


@router.post('/challenge/{challenge_id}/task', tags=['Task'])
async def add_task_under_challenge(challenge_id: int, data: AddTaskInput) -> int:
    return await db.task.add(challenge_id=challenge_id, identifier=data.identifier, selection_type=data.selection_type,
                             problem_id=data.problem_id, peer_review_id=data.peer_review_id)


@router.get('/challenge/{challenge_id}/task', tags=['Task'])
async def browse_task_under_challenge(challenge_id: int) -> Sequence[do.Task]:
    return await db.task.browse(challenge_id=challenge_id)
