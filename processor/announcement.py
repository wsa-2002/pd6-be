from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model


router = APIRouter(
    tags=['Announcement'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddAnnouncementInput(BaseModel):
    title: str
    content: str
    author_id: int
    post_time: model.ServerTZDatetime
    expire_time: model.ServerTZDatetime


@router.post('/announcement')
@enveloped
async def add_announcement(data: AddAnnouncementInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    announcement_id = await service.announcement.add(title=data.title, content=data.content,
                                                     author_id=request.account.id,
                                                     post_time=data.post_time, expire_time=data.expire_time)
    return model.AddOutput(id=announcement_id)


BROWSE_ANNOUNCEMENT_COLUMNS = {
    'id': int,
    'title': str,
    'content': str,
    'author_id': int,
    'post_time': model.ServerTZDatetime,
    'expire_time': model.ServerTZDatetime,
    'is_deleted': bool
}


@router.get('/announcement')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_ANNOUNCEMENT_COLUMNS.items()})
async def browse_announcement(
        req: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - System manager (all)
    - System guest (limited)
    """
    system_role = await rbac.get_role(req.account.id)
    if not system_role >= RoleType.guest:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ANNOUNCEMENT_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ANNOUNCEMENT_COLUMNS)

    announcements, total_count = await service.announcement.browse(limit=limit, offset=offset, filters=filters, sorters=sorters,
                                                                   include_scheduled=system_role >= RoleType.manager, ref_time=req.time)
    return model.BrowseOutputBase(announcements, total_count=total_count)


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
    post_time: model.ServerTZDatetime = None
    expire_time: model.ServerTZDatetime = None


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
