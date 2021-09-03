from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac


router = APIRouter(
    tags=['Email Verification'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.post('/email-verification/{email_verification_id}/resend')
@enveloped
async def resend_verification_email(email_verification_id: int, request: Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    # 因為需要 account_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    email_verification = await service.email_verification.read(email_verification_id=email_verification_id)

    if not (await rbac.validate(request.account.id, RoleType.manager)
            or request.account.id is email_verification.account_id):
        raise exc.NoPermission

    await service.email_verification.resend(email_verification_id=email_verification_id)


@router.delete('/email-verification/{email_verification_id}')
@enveloped
async def delete_pending_email_verification(email_verification_id: int, request: Request) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    # 因為需要 account_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    email_verification = await service.email_verification.read(email_verification_id)

    if not (await rbac.validate(request.account.id, RoleType.manager)
            or request.account.id is email_verification.account_id):
        raise exc.NoPermission

    await service.email_verification.delete(email_verification_id)