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
def browse_peer_reviews():
    return [model.peer_review]


@router.post('/peer-review')
def add_peer_review():
    return {'id': 1}


@router.post('/peer-review/{peer_review_id}')
def read_peer_review(peer_review_id: int):
    return model.peer_review


@router.patch('/peer-review/{peer_review_id}')
def edit_peer_review(peer_review_id: int):
    pass


@router.delete('/peer-review/{peer_review_id}')
def delete_peer_review(peer_review_id: int):
    pass


@router.get('/peer-review/{peer_review_id}/record')
def browse_peer_review_records(peer_review_id: int):
    return [model.peer_review_record]


@router.post('/peer-review/{peer_review_id}/record')
def add_peer_review_record(peer_review_id: int):
    return {'id': 1}


@router.get('/peer-review-record/{peer_review_record_id}/record')
def read_peer_review_record(peer_review_record_id: int):
    return model.peer_review_record


@router.patch('/peer-review-record/{peer_review_record_id}/record')
def edit_peer_review_record(peer_review_record_id: int):
    pass
