from typing import Sequence

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from util import rbac

import fastapi.responses


router = APIRouter(
    tags=['System'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


@router.get('/access-log')
@enveloped
async def browse_access_log(offset: int, limit: int, req: auth.Request) -> Sequence[do.AccessLog]:
    """
    ### 權限
    - Class+ manager
    """
    # if not (await rbac.validate(req.account.id, RoleType.manager)  # System manager
    #         or await db.rbac.any_class_role(member_id=req.account.id, role=RoleType.manager)):  # Any class manager
    #     raise exc.NoPermission

    access_logs = await db.access_log.browse(offset, limit)
    return access_logs
