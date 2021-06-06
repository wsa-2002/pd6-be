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


class AddAnnouncementInput(BaseModel):
    title: str
    content: str
    author_id: int
    post_time: datetime
    expire_time: datetime


@router.post('/announcement')
async def add_announcement(data: AddAnnouncementInput, request: auth.Request) -> int:
    return await db.announcement.add(title=data.title, content=data.content, author_id=request.account.id,
                                     post_time=data.post_time, expire_time=data.expire_time)


@router.get('/announcement')
async def browse_announcement() -> Sequence[do.Announcement]:
    # TODO: check if can see all???
    return await db.announcement.browse(show_hidden=True)


@router.get('/announcement/{announcement_id}')
async def read_announcement(announcement_id: int) -> do.Announcement:
    # TODO: check if can see all???
    return await db.announcement.read(announcement_id, show_hidden=True)


class EditAnnouncementInput(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    post_time: Optional[datetime] = None
    expire_time: Optional[datetime] = None


@router.patch('/announcement/{announcement_id}')
async def edit_announcement(announcement_id: int, data: EditAnnouncementInput) -> None:
    return await db.announcement.edit(announcement_id=announcement_id, title=data.title, content=data.content,
                                      post_time=data.post_time, expire_time=data.expire_time)


@router.delete('/announcement/{announcement_id}')
async def delete_announcement(announcement_id: int) -> None:
    return await db.announcement.delete(announcement_id=announcement_id)
