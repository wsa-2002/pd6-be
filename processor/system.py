from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac, model


router = APIRouter(
    tags=['System'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/access-log')
@enveloped
async def browse_access_log(
        req: Request,
        limit: model.Limit, offset: model.Offset,
        access_time: model.FilterStr = None,
        request_method: model.FilterStr = None,
        resource_path: model.FilterStr = None,
        ip: model.FilterStr = None,
        account_id: model.FilterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - Class+ manager
    """
    if not (await rbac.validate(req.account.id, RoleType.manager)  # System manager
            # or await rbac.any_class_role(member_id=req.account.id, role=RoleType.manager)):  # Any class manager
            ):
        raise exc.NoPermission

    access_time = model.parse_filter(access_time, model.UTCDatetime)
    request_method = model.parse_filter(request_method, str)
    resource_path = model.parse_filter(resource_path, str)
    ip = model.parse_filter(ip, str)
    account_id = model.parse_filter(account_id, int)

    access_logs, total_count = await service.access_log.browse(
        limit=limit, offset=offset,
        access_time=access_time,
        request_method=request_method,
        resource_path=resource_path,
        ip=ip,
        account_id=account_id,
    )
    return model.BrowseOutputBase(access_logs, total_count=total_count)
