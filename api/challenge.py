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
    tags=['Challenge'],
    default_response_class=envelope.JSONResponse,
)


class AddChallengeInput(BaseModel):
    class_id: int
    type: enum.ChallengeType
    publicize_type: enum.ChallengePublicizeType
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_hidden: bool


@router.post('/class/{class_id}/challenge', tags=['Course'])
async def add_challenge_under_class(class_id: int, data: AddChallengeInput, request: auth.Request) -> int:
    if not (await rbac.validate(request.account.id, RoleType.normal, class_id=class_id, inherit=False)
            or await rbac.validate(request.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    challenge_id = await db.challenge.add(
        class_id=class_id, type_=data.type, publicize_type=data.publicize_type, title=data.title,
        setter_id=request.account.id,
        description=data.description, start_time=data.start_time, end_time=data.end_time, is_hidden=data.is_hidden,
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
    type: enum.ChallengeType = None
    publicize_type: enum.ChallengePublicizeType = None
    title: str = None
    description: Optional[str] = ...
    start_time: datetime = None
    end_time: datetime = None
    is_hidden: bool = None


@router.patch('/challenge/{challenge_id}')
async def edit_challenge(challenge_id: int, data: EditChallengeInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    await db.challenge.edit(challenge_id=challenge_id, type_=data.type, publicize_type=data.publicize_type,
                            title=data.title, description=data.description, start_time=data.start_time,
                            end_time=data.end_time, is_hidden=data.is_hidden)


@router.delete('/challenge/{challenge_id}')
async def delete_challenge(challenge_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    await db.challenge.delete(challenge_id)


class AddProblemInput(BaseModel):
    challenge_label: str
    selection_type: enum.TaskSelectionType
    title: str
    full_score: int
    description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_hidden: bool


@router.post('/challenge/{challenge_id}/problem', tags=['Problem'])
async def add_problem_under_challenge(challenge_id: int, data: AddProblemInput, request: auth.Request) -> int:
    problem_id = await db.problem.add(
        challenge_id=challenge_id, challenge_label=data.challenge_label, selection_type=data.selection_type,
        title=data.title, setter_id=request.account.id, full_score=data.full_score,
        description=data.description, source=data.source, hint=data.hint, is_hidden=data.is_hidden,
    )

    return problem_id


class AddPeerReviewInput(BaseModel):
    challenge_label: str
    target_problem_id: int
    description: str
    min_score: int
    max_score: int
    max_review_count: int
    start_time: datetime
    end_time: datetime
    is_hidden: bool


@router.post('/challenge/{challenge_id}/peer-review', tags=['Peer Review'])
async def add_peer_review_under_challenge(challenge_id: int, data: AddPeerReviewInput, request: auth.Request) -> int:
    # validate problem belongs to same class
    target_problem = await db.problem.read(problem_id=data.target_problem_id)
    target_problem_challenge = await db.challenge.read(target_problem.challenge_id)

    current_challenge = await db.challenge.read(challenge_id)

    # Only allow peer review to target to same class
    if current_challenge.class_id is not target_problem_challenge.class_id:
        raise exc.IllegalInput

    return await db.peer_review.add(challenge_id=challenge_id,
                                    challenge_label=data.challenge_label,
                                    target_problem_id=data.target_problem_id,
                                    setter_id=request.account.id,
                                    description=data.description,
                                    min_score=data.min_score, max_score=data.max_score,
                                    max_review_count=data.max_review_count,
                                    start_time=data.start_time, end_time=data.end_time,
                                    is_hidden=data.is_hidden)


@dataclass
class BrowseTaskOutput:
    problem: Sequence[do.Problem]
    peer_review: Sequence[do.PeerReview]


@router.get('/challenge/{challenge_id}/task')
async def browse_task_under_challenge(challenge_id: int) -> BrowseTaskOutput:
    return BrowseTaskOutput(
        problem=await db.problem.browse_by_challenge(challenge_id=challenge_id),
        peer_review=await db.peer_review.browse_by_challenge(challenge_id=challenge_id),
    )
