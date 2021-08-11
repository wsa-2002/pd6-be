from dataclasses import dataclass
from uuid import UUID

import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac


router = APIRouter(
    tags=['S3 File'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class S3FileUrlOutput:
    url: str


@router.get('/s3-file/{s3_file_uuid}/url')
@enveloped
async def get_s3_file_url(s3_file_uuid: UUID, as_attachment: bool, request: Request) -> S3FileUrlOutput:
    """
    ### 權限
    - SN

    ### Note
    - 目前所有 url 都有時間限制 (超時會自動過期)
    """
    if not await rbac.validate(request.account.id, min_role=RoleType.normal):
        raise exc.NoPermission

    s3_file = await service.s3_file.read(s3_file_uuid=s3_file_uuid)
    return S3FileUrlOutput(url=await service.s3_file.sign_url(s3_file=s3_file, as_attachment=as_attachment))
