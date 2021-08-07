from typing import Sequence

from base import do
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
from .util import rbac

from .. import service


router = APIRouter(
    tags=['System'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/access-log')
@enveloped
async def browse_access_log(offset: int, limit: int, req: Request) -> Sequence[do.AccessLog]:
    """
    ### 權限
    - Class+ manager
    """
    if not (await rbac.validate(req.account.id, RoleType.manager)  # System manager
            # or await rbac.any_class_role(member_id=req.account.id, role=RoleType.manager)):  # Any class manager
            ):
        raise exc.NoPermission

    access_logs = await service.access_log.browse(offset, limit)
    return access_logs
