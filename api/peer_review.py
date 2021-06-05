from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

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


@router.get('/peer-review')
async def browse_peer_reviews() -> Sequence[do.PeerReview]:
    return await db.peer_review.browse()


class AddPeerReviewInput(BaseModel):
    target_task_id: int
    description: str
    min_score: int
    max_score: int
    max_review_count: int
    start_time: datetime
    end_time: datetime
    is_enabled: bool
    is_hidden: bool


@router.post('/peer-review')
async def add_peer_review(data: AddPeerReviewInput, request: auth.Request) -> int:
    return await db.peer_review.add(target_task_id=data.target_task_id,
                                    setter_id=request.account.id,
                                    description=data.description,
                                    min_score=data.min_score, max_score=data.max_score,
                                    max_review_count=data.max_review_count,
                                    start_time=data.start_time, end_time=data.end_time,
                                    is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.get('/peer-review/{peer_review_id}')
async def read_peer_review(peer_review_id: int) -> do.PeerReview:
    return await db.peer_review.read(peer_review_id=peer_review_id)


class EditPeerReviewInput(BaseModel):
    description: str
    min_score: int
    max_score: int
    max_review_count: int
    start_time: datetime
    end_time: datetime
    is_enabled: bool
    is_hidden: bool


@router.patch('/peer-review/{peer_review_id}')
async def edit_peer_review(peer_review_id: int, data: EditPeerReviewInput) -> None:
    return await db.peer_review.edit(peer_review_id=peer_review_id,
                                     description=data.description,
                                     min_score=data.min_score, max_score=data.max_score,
                                     max_review_count=data.max_review_count,
                                     start_time=data.start_time, end_time=data.end_time,
                                     is_enabled=data.is_enabled, is_hidden=data.is_hidden)


@router.delete('/peer-review/{peer_review_id}')
async def delete_peer_review(peer_review_id: int) -> None:
    return await db.peer_review.delete(peer_review_id=peer_review_id)


@router.get('/peer-review/{peer_review_id}/record')
async def browse_peer_review_records(peer_review_id: int):
    return [model.peer_review_record]


# 改一下這些 function name
@router.post('/peer-review/{peer_review_id}/record')
async def assign_peer_review_record(peer_review_id: int):
    """
    發互評 (決定 A 要評誰 )
    """
    return {'id': 1}


@router.get('/peer-review-record/{peer_review_record_id}')
async def read_peer_review_record(peer_review_record_id: int):
    return model.peer_review_record


@router.put('/peer-review-record/{peer_review_record_id}/score')
async def submit_peer_review_record_score(peer_review_record_id: int):
    """
    互評完了，交互評成績評語
    """
    pass
