from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
from persistence import database as db, email
import service
from util.context import context

router = APIRouter(
    tags=['Email Verification'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.post('/email-verification/{email_verification_id}/resend')
@enveloped
async def resend_email_verification(email_verification_id: int) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    # 因為需要 account_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    email_verification = await db.email_verification.read(email_verification_id=email_verification_id)

    if not (await service.rbac.validate_system(context.account.id, RoleType.manager)
            or context.account.id == email_verification.account_id):
        raise exc.NoPermission

    account = await db.account.read(email_verification.account_id)

    email_verification = await db.email_verification.read(email_verification_id)
    code = await db.email_verification.read_verification_code(email_verification_id)
    await email.verification.send(to=email_verification.email, code=code, username=account.username)


@router.delete('/email-verification/{email_verification_id}')
@enveloped
async def delete_pending_email_verification(email_verification_id: int) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    # 因為需要 account_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    email_verification = await db.email_verification.read(email_verification_id)

    if not (await service.rbac.validate_system(context.account.id, RoleType.manager)
            or context.account.id == email_verification.account_id):
        raise exc.NoPermission

    await db.email_verification.delete(email_verification_id)
