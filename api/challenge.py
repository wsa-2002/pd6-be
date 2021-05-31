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
    tags=['Challenge'],
    default_response_class=envelope.JSONResponse,
)


class CreateChallengeInput(BaseModel):
    class_id: int
    type: enum.ChallengeType
    name: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_enabled: bool
    is_hidden: bool


@router.post('/class/{class_id}/challenge', tags=['Course'])
def create_challenge_under_class(class_id: int, data: CreateChallengeInput, request: auth.Request) -> int:
    if not (await rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False)
            or await rbac.validate(request.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    challenge_id = await db.challenge.add(
        class_id=class_id, type_=data.type, name=data.name, setter_id=request.account.id, description=data.description,
        start_time=data.start_time, end_time=data.end_time, is_enabled=data.is_enabled, is_hidden=data.is_hidden,
    )
    return challenge_id


@router.get('/class/{class_id}/challenge', tags=['Course'])
def get_challenges_under_class(class_id: int, request: auth.Request) -> Sequence[db.challenge.do.Challenge]:
    if not rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False):
        raise exc.NoPermission

    challenges = await db.class_.browse_challenges(class_id=class_id)
    return challenges


@router.get('/challenge')
def get_challenges(request: auth.Request) -> Sequence[db.challenge.do.Challenge]:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    challenges = await db.challenge.browse()
    return challenges


@router.get('/challenge/{challenge_id}')
@util.enveloped
def get_challenge(challenge_id: int, request: auth.Request) -> db.challenge.do.Challenge:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    challenge = await db.challenge.read(challenge_id=challenge_id)
    return challenge


class ModifyChallengeInput(BaseModel):
    # class_id: int
    type: Optional[enum.ChallengeType]
    name: Optional[str]
    description: Optional[str] = ...
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_enabled: Optional[bool]
    is_hidden: Optional[bool]


@router.patch('/challenge/{challenge_id}')
def modify_challenge(challenge_id: int, data: ModifyChallengeInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    await db.challenge.edit(challenge_id=challenge_id, type_=data.type, name=data.name,
                            description=data.description, start_time=data.start_time, end_time=data.end_time,
                            is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.delete('/challenge/{challenge_id}')
def remove_challenge(challenge_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    # TODO


@router.post('/challenge/{challenge_id}/problem')
@util.enveloped
def create_problem_under_challenge(challenge_id: int):
    return {'id': 1}


@router.get('/challenge/{challenge_id}/problem')
@util.enveloped
def get_problems_under_challenge(challenge_id: int):
    return [model.problem]
