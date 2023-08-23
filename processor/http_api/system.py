from typing import Sequence

from base.enum import RoleType
from base import do
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
from persistence import database as db
import service
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['System'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)

BROWSE_ACCESS_LOG_COLUMNS = {
    'access_time': model.ServerTZDatetime,
    'request_method': str,
    'resource_path': str,
    'ip': str,
    'account_id': int,
}


class BrowseAccessLogOutput(model.BrowseOutputBase):
    data: Sequence[do.AccessLog]


@router.get('/access-log')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCESS_LOG_COLUMNS.items()})
async def browse_access_log(
        limit: model.Limit, offset: model.Offset,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseAccessLogOutput:
    """
    ### 權限
    - Class+ manager
    
    ### Available columns
    """
    if not (await service.rbac.validate_system(context.account.id, RoleType.manager)  # System manager
            # or await rbac.any_class_role(member_id=context.account.id, role=RoleType.manager)):  # Any class manager
    ):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ACCESS_LOG_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ACCESS_LOG_COLUMNS)

    access_logs, total_count = await db.access_log.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)
    return BrowseAccessLogOutput(access_logs, total_count=total_count)
