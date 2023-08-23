from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
from persistence import database as db
import service
import util
from util import model
from util.context import context

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
async def add_announcement(data: AddAnnouncementInput) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    announcement_id = await db.announcement.add(title=data.title, content=data.content,
                                                author_id=context.account.id,
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


class BrowseAnnouncementOutput(model.BrowseOutputBase):
    data: Sequence[do.Announcement]


@router.get('/announcement')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_ANNOUNCEMENT_COLUMNS.items()})
async def browse_announcement(
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseAnnouncementOutput:
    """
    ### 權限
    - System manager (all)
    - System guest (limited)

    ### Available columns
    """
    system_role = await service.rbac.get_system_role(context.account.id)
    if not system_role >= RoleType.guest:
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_ANNOUNCEMENT_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_ANNOUNCEMENT_COLUMNS)

    announcements, total_count = await db.announcement.browse(limit=limit, offset=offset,
                                                              filters=filters, sorters=sorters,
                                                              exclude_scheduled=system_role < RoleType.manager,
                                                              ref_time=context.request_time)
    return BrowseAnnouncementOutput(announcements, total_count=total_count)


@router.get('/announcement/{announcement_id}')
@enveloped
async def read_announcement(announcement_id: int) -> do.Announcement:
    """
    ### 權限
    - System manager (all)
    - System guest (limited)
    """
    system_role = await service.rbac.get_system_role(context.account.id)
    if not system_role >= RoleType.guest:
        raise exc.NoPermission

    return await db.announcement.read(announcement_id,
                                      exclude_scheduled=system_role < RoleType.manager, ref_time=context.request_time)


class EditAnnouncementInput(BaseModel):
    title: str = None
    content: str = None
    post_time: model.ServerTZDatetime = None
    expire_time: model.ServerTZDatetime = None


@router.patch('/announcement/{announcement_id}')
@enveloped
async def edit_announcement(announcement_id: int, data: EditAnnouncementInput) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.announcement.edit(announcement_id=announcement_id, title=data.title, content=data.content,
                                      post_time=data.post_time, expire_time=data.expire_time)


@router.delete('/announcement/{announcement_id}')
@enveloped
async def delete_announcement(announcement_id: int) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.announcement.delete(announcement_id=announcement_id)
