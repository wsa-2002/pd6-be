from dataclasses import dataclass
from uuid import UUID

import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from persistence import s3
import service
from util.context import context

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
async def get_s3_file_url(s3_file_uuid: UUID, filename: str, as_attachment: bool) -> S3FileUrlOutput:
    """
    ### 權限
    - SN

    ### Note
    - 目前所有 url 都有時間限制 (超時會自動過期)
    """
    if not await service.rbac.validate_system(context.account.id, min_role=RoleType.normal):
        raise exc.NoPermission
    try:  # 先摸 db 看有沒有這個 file
        s3_file = await db.s3_file.read(s3_file_uuid=s3_file_uuid)
        return S3FileUrlOutput(url=await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                                           filename=filename, as_attachment=as_attachment))
    except exc.persistence.NotFound:  # 如果 db 找不到的話就代表在 temp 裡面
        return S3FileUrlOutput(url=await s3.tools.sign_url(bucket='temp', key=str(s3_file_uuid),
                                                           filename=filename, as_attachment=as_attachment))
