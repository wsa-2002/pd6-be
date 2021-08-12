from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do, enum
from base.cls import NoTimezoneIsoDatetime
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac, model


router = APIRouter(
    tags=['Challenge'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddChallengeInput(BaseModel):
    type: enum.ChallengeType
    publicize_type: enum.ChallengePublicizeType
    title: str
    description: Optional[str]
    start_time: NoTimezoneIsoDatetime
    end_time: NoTimezoneIsoDatetime


@router.post('/class/{class_id}/challenge', tags=['Course'])
@enveloped
async def add_challenge_under_class(class_id: int, data: AddChallengeInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    challenge_id = await service.challenge.add(
        class_id=class_id, type_=data.type, publicize_type=data.publicize_type,
        title=data.title, setter_id=request.account.id, description=data.description,
        start_time=data.start_time, end_time=data.end_time
    )
    return model.AddOutput(id=challenge_id)


@router.get('/class/{class_id}/challenge', tags=['Course'])
@enveloped
async def browse_challenge_under_class(class_id: int, request: Request) -> Sequence[do.Challenge]:
    """
    ### 權限
    - Class manager (all)
    - Class guest (not scheduled)
    """
    class_role = await rbac.get_role(request.account.id, class_id=class_id)

    if class_role < RoleType.guest:
        raise exc.NoPermission

    return await service.challenge.browse(class_id=class_id,
                                          include_scheduled=(class_role == RoleType.manager), ref_time=request.time)


@router.get('/challenge/{challenge_id}')
@enveloped
async def read_challenge(challenge_id: int, request: Request) -> do.Challenge:
    """
    ### 權限
    - Class manager (all)
    - Class guest (not scheduled)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await service.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    if class_role < RoleType.guest or (class_role < RoleType.manager and request.time < challenge.start_time):
        raise exc.NoPermission

    return challenge


class EditChallengeInput(BaseModel):
    # class_id: int
    type: enum.ChallengeType = None
    publicize_type: enum.ChallengePublicizeType = None
    title: str = None
    description: Optional[str] = ...
    start_time: NoTimezoneIsoDatetime = None
    end_time: NoTimezoneIsoDatetime = None


@router.patch('/challenge/{challenge_id}')
@enveloped
async def edit_challenge(challenge_id: int, data: EditChallengeInput, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await service.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await service.challenge.edit(challenge_id=challenge_id, type_=data.type, publicize_type=data.publicize_type,
                                 title=data.title, description=data.description, start_time=data.start_time,
                                 end_time=data.end_time)


@router.delete('/challenge/{challenge_id}')
@enveloped
async def delete_challenge(challenge_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await service.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await service.challenge.delete(challenge_id)


class AddProblemInput(BaseModel):
    challenge_label: str
    selection_type: enum.TaskSelectionType
    title: str
    full_score: int
    description: Optional[str]
    source: Optional[str]
    hint: Optional[str]


@router.post('/challenge/{challenge_id}/problem', tags=['Problem'])
@enveloped
async def add_problem_under_challenge(challenge_id: int, data: AddProblemInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await service.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    problem_id = await service.problem.add(
        challenge_id=challenge_id, challenge_label=data.challenge_label, selection_type=data.selection_type,
        title=data.title, setter_id=request.account.id, full_score=data.full_score,
        description=data.description, source=data.source, hint=data.hint,
    )

    return model.AddOutput(id=problem_id)


class AddEssayInput(BaseModel):
    challenge_id: int
    challenge_label: str
    title: str
    description: Optional[str]


@router.post('/challenge/{challenge_id}/essay', tags=['Essay'])
@enveloped
async def add_essay_under_challenge(challenge_id: int, data: AddEssayInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await service.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    essay_id = await service.essay.add(challenge_id=data.challenge_id, challenge_label=data.challenge_label,
                                       title=data.title, setter_id=request.account.id, description=data.description)
    return model.AddOutput(id=essay_id)


class AddPeerReviewInput(BaseModel):
    challenge_label: str
    target_problem_id: int
    description: str
    min_score: int
    max_score: int
    max_review_count: int
    start_time: NoTimezoneIsoDatetime
    end_time: NoTimezoneIsoDatetime


@router.post('/challenge/{challenge_id}/peer-review', tags=['Peer Review'])
@enveloped
async def add_peer_review_under_challenge(challenge_id: int, data: AddPeerReviewInput, request: Request) \
        -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await service.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    # validate problem belongs to same class
    target_problem = await service.problem.read(problem_id=data.target_problem_id)
    target_problem_challenge = await service.challenge.read(target_problem.challenge_id)

    # Only allow peer review to target to same class
    if challenge.class_id is not target_problem_challenge.class_id:
        raise exc.IllegalInput

    peer_review_id = await service.peer_review.add(challenge_id=challenge_id,
                                                   challenge_label=data.challenge_label,
                                                   target_problem_id=data.target_problem_id,
                                                   setter_id=request.account.id,
                                                   description=data.description,
                                                   min_score=data.min_score, max_score=data.max_score,
                                                   max_review_count=data.max_review_count,
                                                   start_time=data.start_time, end_time=data.end_time)
    return model.AddOutput(id=peer_review_id)


@dataclass
class BrowseTaskOutput:
    problem: Sequence[do.Problem]
    peer_review: Sequence[do.PeerReview]
    essay: Sequence[do.Essay]


@router.get('/challenge/{challenge_id}/task')
@enveloped
async def browse_task_under_challenge(challenge_id: int, request: Request) -> BrowseTaskOutput:
    """
    ### 權限
    - Class manager (all)
    - Class guest (active/archived challenges)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await service.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    problems, peer_reviews, essays = service.challenge.browse_task(challenge.id)

    return BrowseTaskOutput(
        problem=problems,
        peer_review=peer_reviews,
        essay=essays,
    )