from datetime import datetime
from typing import Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Announcement'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


class AddAnnouncementInput(BaseModel):
    title: str
    content: str
    author_id: int
    post_time: datetime
    expire_time: datetime


@router.post('/announcement')
@enveloped
async def add_announcement(data: AddAnnouncementInput, request: auth.Request) -> int:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.announcement.add(title=data.title, content=data.content, author_id=request.account.id,
                                     post_time=data.post_time, expire_time=data.expire_time)


@router.get('/announcement')
@enveloped
async def browse_announcement(request: auth.Request) -> Sequence[do.Announcement]:
    """
    ### 權限
    - System manager (all)
    - System guest (limited)
    """
    system_role = await rbac.get_role(request.account.id)
    if not system_role >= RoleType.guest:
        raise exc.NoPermission

    return await db.announcement.browse(include_scheduled=system_role >= RoleType.manager)


@router.get('/announcement/{announcement_id}')
@enveloped
async def read_announcement(announcement_id: int, request: auth.Request) -> do.Announcement:
    """
    ### 權限
    - System manager (all)
    - System guest (limited)
    """
    system_role = await rbac.get_role(request.account.id)
    if not system_role >= RoleType.guest:
        raise exc.NoPermission

    return await db.announcement.read(announcement_id, include_scheduled=system_role >= RoleType.manager)


class EditAnnouncementInput(BaseModel):
    title: str = None
    content: str = None
    post_time: datetime = None
    expire_time: datetime = None


@router.patch('/announcement/{announcement_id}')
@enveloped
async def edit_announcement(announcement_id: int, data: EditAnnouncementInput, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.announcement.edit(announcement_id=announcement_id, title=data.title, content=data.content,
                                      post_time=data.post_time, expire_time=data.expire_time)


@router.delete('/announcement/{announcement_id}')
@enveloped
async def delete_announcement(announcement_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.announcement.delete(announcement_id=announcement_id)
