from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import CourseType, RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Peer Review'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/peer-review/{peer_review_id}')
async def read_peer_review(peer_review_id: int, request: auth.Request) -> do.PeerReview:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await db.peer_review.read(peer_review_id, include_hidden=True)
    challenge = await db.challenge.read(peer_review.challenge_id, include_hidden=True)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    if (peer_review.is_hidden and class_role < RoleType.manager  # hidden => need manager
            or not peer_review.is_hidden and class_role < RoleType.normal):  # not hidden => need normal
        raise exc.NoPermission

    return peer_review


class EditPeerReviewInput(BaseModel):
    description: str = None
    min_score: int = None
    max_score: int = None
    max_review_count: int = None
    start_time: datetime = None
    end_time: datetime = None
    is_hidden: bool = None


@router.patch('/peer-review/{peer_review_id}')
async def edit_peer_review(peer_review_id: int, data: EditPeerReviewInput, request: auth.Request) -> None:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await db.peer_review.read(peer_review_id, include_hidden=True)
    challenge = await db.challenge.read(peer_review.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await db.peer_review.edit(peer_review_id=peer_review_id,
                                     description=data.description,
                                     min_score=data.min_score, max_score=data.max_score,
                                     max_review_count=data.max_review_count,
                                     start_time=data.start_time, end_time=data.end_time,
                                     is_hidden=data.is_hidden)


@router.delete('/peer-review/{peer_review_id}')
async def delete_peer_review(peer_review_id: int, request: auth.Request) -> None:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await db.peer_review.read(peer_review_id, include_hidden=True)
    challenge = await db.challenge.read(peer_review.challenge_id, include_hidden=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await db.peer_review.delete(peer_review_id=peer_review_id)


@router.get('/peer-review/{peer_review_id}/record')
async def browse_peer_review_record(peer_review_id: int, request: auth.Request):
    return [model.peer_review_record]


# 改一下這些 function name
@router.post('/peer-review/{peer_review_id}/record')
async def assign_peer_review_record(peer_review_id: int, request: auth.Request):
    """
    發互評 (決定 A 要評誰 )
    """
    return {'id': 1}


@router.get('/peer-review-record/{peer_review_record_id}')
async def read_peer_review_record(peer_review_record_id: int, request: auth.Request):
    return model.peer_review_record


@router.put('/peer-review-record/{peer_review_record_id}/score')
async def submit_peer_review_record_score(peer_review_record_id: int, request: auth.Request):
    """
    互評完了，交互評成績評語
    """
    pass
