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
    tags=['Announcement'],
    default_response_class=envelope.JSONResponse,
)


@router.post('/announcement')
def add_announcement():
    return {'id': 1}


@router.get('/announcement')
def browse_announcements():
    return [ann_1, ann_2]


@router.get('/announcement/{announcement_id}')
def read_announcement(announcement_id: int):
    if announcement_id is 1:
        return ann_1
    elif announcement_id is 2:
        return ann_2
    else:
        raise Exception


@router.patch('/announcement/{announcement_id}')
def edit_announcement(announcement_id: int):
    pass


@router.delete('/announcement/{announcement_id}')
def delete_announcement(announcement_id: int):
    pass
