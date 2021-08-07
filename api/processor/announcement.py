from typing import Sequence

from pydantic import BaseModel

from base import do
from base.cls import NoTimezoneIsoDatetime
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
from util import rbac

from .. import service

router = APIRouter(
    tags=['Announcement'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddAnnouncementInput(BaseModel):
    title: str
    content: str
    author_id: int
    post_time: NoTimezoneIsoDatetime
    expire_time: NoTimezoneIsoDatetime


@router.post('/announcement')
@enveloped
async def add_announcement(data: AddAnnouncementInput, request: Request) -> int:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await service.announcement.add(title=data.title, content=data.content, author_id=request.account.id,
                                          post_time=data.post_time, expire_time=data.expire_time)


@router.get('/announcement')
@enveloped
async def browse_announcement(request: Request) -> Sequence[do.Announcement]:
    """
    ### 權限
    - System manager (all)
    - System guest (limited)
    """
    system_role = await rbac.get_role(request.account.id)
    if not system_role >= RoleType.guest:
        raise exc.NoPermission

    return await service.announcement.browse(include_scheduled=system_role >= RoleType.manager, ref_time=request.time)


@router.get('/announcement/{announcement_id}')
@enveloped
async def read_announcement(announcement_id: int, request: Request) -> do.Announcement:
    """
    ### 權限
    - System manager (all)
    - System guest (limited)
    """
    system_role = await rbac.get_role(request.account.id)
    if not system_role >= RoleType.guest:
        raise exc.NoPermission

    return await service.announcement.read(announcement_id,
                                           include_scheduled=system_role >= RoleType.manager, ref_time=request.time)


class EditAnnouncementInput(BaseModel):
    title: str = None
    content: str = None
    post_time: NoTimezoneIsoDatetime = None
    expire_time: NoTimezoneIsoDatetime = None


@router.patch('/announcement/{announcement_id}')
@enveloped
async def edit_announcement(announcement_id: int, data: EditAnnouncementInput, request: Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await service.announcement.edit(announcement_id=announcement_id, title=data.title, content=data.content,
                                           post_time=data.post_time, expire_time=data.expire_time)


@router.delete('/announcement/{announcement_id}')
@enveloped
async def delete_announcement(announcement_id: int, request: Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await service.announcement.delete(announcement_id=announcement_id)
