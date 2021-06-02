from datetime import datetime
from typing import Optional, Sequence, Collection

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
    name: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_enabled: bool
    is_hidden: bool


@router.post('/class/{class_id}/challenge', tags=['Course'])
def add_challenge_under_class(class_id: int, data: AddChallengeInput, request: auth.Request) -> int:
    if not (await rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False)
            or await rbac.validate(request.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    challenge_id = await db.challenge.add(
        class_id=class_id, type_=data.type, name=data.name, setter_id=request.account.id, description=data.description,
        start_time=data.start_time, end_time=data.end_time, is_enabled=data.is_enabled, is_hidden=data.is_hidden,
    )
    return challenge_id


@router.get('/class/{class_id}/challenge', tags=['Course'])
def browse_challenges_under_class(class_id: int, request: auth.Request) -> Sequence[do.Challenge]:
    if not rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False):
        raise exc.NoPermission

    challenges = await db.challenge.browse(class_id=class_id)
    return challenges


@router.get('/challenge')
def browse_challenges(request: auth.Request) -> Sequence[do.Challenge]:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    challenges = await db.challenge.browse()
    return challenges


@router.get('/challenge/{challenge_id}')
def read_challenge(challenge_id: int, request: auth.Request) -> do.Challenge:
    if not request.account.role.is_manager:
        raise exc.NoPermission

    challenge = await db.challenge.read(challenge_id=challenge_id)
    return challenge


class EditChallengeInput(BaseModel):
    # class_id: int
    type: Optional[enum.ChallengeType]
    name: Optional[str]
    description: Optional[str] = ...
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_enabled: Optional[bool]
    is_hidden: Optional[bool]


@router.patch('/challenge/{challenge_id}')
def edit_challenge(challenge_id: int, data: EditChallengeInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    await db.challenge.edit(challenge_id=challenge_id, type_=data.type, name=data.name,
                            description=data.description, start_time=data.start_time, end_time=data.end_time,
                            is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.delete('/challenge/{challenge_id}')
def delete_challenge(challenge_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    # TODO


class CreateProblemInput(BaseModel):
    type: enum.ProblemType
    name: str
    full_score: int
    description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_enabled: bool
    is_hidden: bool


@router.post('/challenge/{challenge_id}/problem', tags=['Problem'])
def add_problem_under_challenge(challenge_id: int, data: CreateProblemInput, request: auth.Request) -> int:
    # FIXME: not atomic operation...
    problem_id = await db.problem.add(type_=data.type, name=data.name, setter_id=request.account.id,
                                      full_score=data.full_score, description=data.description, source=data.source,
                                      hint=data.hint, is_enabled=data.is_enabled, is_hidden=data.is_hidden)
    await db.challenge.add_problem_relation(challenge_id=challenge_id, problem_id=problem_id)

    return problem_id


@router.get('/challenge/{challenge_id}/problem')
def browse_problems_under_challenge(challenge_id: int) -> Collection[do.Problem]:
    return await db.problem.browse_by_challenge(challenge_id=challenge_id)
