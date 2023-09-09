import pydantic
from dataclasses import dataclass
from typing import Sequence, Optional
from uuid import UUID

from pydantic import BaseModel

from base.enum import RoleType
from base import do
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from persistence import email
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Account'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class BrowseAccountOutput:
    id: int
    username: str
    nickname: str
    role: str
    real_name: str
    alternative_email: Optional[str]

    student_id: Optional[str]


BROWSE_ACCOUNT_COLUMNS = {
    'id': int,
    'username': str,
    'nickname': str,
    'role': str,
    'real_name': str,
    'alternative_email': str,
}


class BrowseAccountWithDefaultStudentIdOutput(util.model.BrowseOutputBase):
    data: Sequence[BrowseAccountOutput]


@router.get('/account')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCOUNT_COLUMNS.items()})
async def browse_account_with_default_student_id(
        limit: util.model.Limit = 50, offset: util.model.Offset = 0,
        filter: util.model.FilterStr = None, sort: util.model.SorterStr = None,
) -> BrowseAccountWithDefaultStudentIdOutput:

    """
    ### 權限
    - System Manager
    """
    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    if not is_manager:
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_ACCOUNT_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_ACCOUNT_COLUMNS)

    result, total_count = await db.account_vo.browse_with_default_student_card(limit=limit, offset=offset,
                                                                               filters=filters, sorters=sorters)
    data = [BrowseAccountOutput(id=account.id, username=account.username, nickname=account.nickname,
                                role=account.role, real_name=account.real_name,
                                alternative_email=account.alternative_email, student_id=student_card.student_id)
            for account, student_card in result]

    return BrowseAccountWithDefaultStudentIdOutput(data, total_count=total_count)


@dataclass
class BatchGetAccountOutput:
    id: int
    username: str
    real_name: str

    student_id: Optional[str]


@router.get('/account-summary/batch')
@enveloped
async def batch_get_account_with_default_student_id(account_ids: pydantic.Json) \
        -> Sequence[BatchGetAccountOutput]:
    """
    ### 權限
    - System Normal

    ### Notes
    - `account_ids`: list of int
    """
    account_ids = pydantic.parse_obj_as(list[int], account_ids)
    if not account_ids:
        return []

    is_normal = await service.rbac.validate_system(context.account.id, RoleType.normal)
    if not is_normal:
        raise exc.NoPermission

    result = await db.account_vo.browse_list_with_default_student_card(account_ids=account_ids)
    return [BatchGetAccountOutput(id=account.id, username=account.username, real_name=account.real_name,
                                  student_id=student_card.student_id)
            for account, student_card in result]


@router.get('/account-summary/batch-by-account-referral')
@enveloped
async def batch_get_account_by_account_referrals(account_referrals: pydantic.Json) \
        -> Sequence[BatchGetAccountOutput]:
    """
    ### 權限
    - System Normal

    ### Notes:
    account_referrals: list of string
    """
    account_referrals = pydantic.parse_obj_as(list[str], account_referrals)
    if not account_referrals:
        return []

    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    result = await db.account_vo.batch_read_by_account_referral(account_referrals=account_referrals)
    return [BatchGetAccountOutput(id=account.id, username=account.username, real_name=account.real_name,
                                  student_id=student_card.student_id)
            for account, student_card in result]


@dataclass
class BrowseAccountWithRoleOutput:
    member_id: int
    role: RoleType
    class_id: int
    class_name: str
    course_id: int
    course_name: str


@router.get('/account/{account_id}/class')
@enveloped
async def browse_all_account_with_class_role(account_id: int) \
        -> Sequence[BrowseAccountWithRoleOutput]:
    """
    ### 權限
    - Self

    ### Available columns
    """
    if account_id != context.account.id:
        raise exc.NoPermission
    results = await db.class_.browse_role_by_account_id(account_id=account_id)

    return [BrowseAccountWithRoleOutput(member_id=class_member.member_id,
                                        role=class_member.role,
                                        class_id=class_member.class_id,
                                        class_name=class_.name,
                                        course_id=course.id,
                                        course_name=course.name)
            for class_member, class_, course in results]


@dataclass
class GetAccountTemplateOutput:
    s3_file_uuid: UUID
    filename: str


@router.get('/account/template')
@enveloped
async def get_account_template_file() -> GetAccountTemplateOutput:
    """
    ### 權限
    - System Manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    s3_file, filename = await service.csv.get_account_template()
    return GetAccountTemplateOutput(s3_file_uuid=s3_file.uuid, filename=filename)


@dataclass
class ReadAccountOutput:
    id: int
    username: str
    nickname: str
    role: Optional[str]
    real_name: Optional[str]
    alternative_email: Optional[str]

    student_id: Optional[str]


@router.get('/account/{account_id}')
@enveloped
async def read_account_with_default_student_id(account_id: int) -> ReadAccountOutput:
    """
    ### 權限
    - System Manager
    - Self
    - System Normal (個資除外)
    """
    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    is_normal = await service.rbac.validate_system(context.account.id, RoleType.normal)
    is_self = context.account.id == account_id

    if not (is_manager or is_normal or is_self):
        raise exc.NoPermission

    view_personal = is_self or is_manager

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    result = ReadAccountOutput(
        id=account.id,
        username=account.username,
        nickname=account.nickname,
        role=account.role,
        real_name=account.real_name,
        alternative_email=account.alternative_email if view_personal else None,
        student_id=student_card.student_id,
    )

    return result


class EditAccountInput(BaseModel):
    username: model.TrimmedNonEmptyStr = None
    nickname: str = None
    alternative_email: Optional[util.model.CaseInsensitiveEmailStr] = util.model.can_omit
    real_name: str = None


@router.patch('/account/{account_id}')
@enveloped
async def edit_account(account_id: int, data: EditAccountInput) -> None:
    """
    ### 權限
    - System Manager
    - Self
    """
    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    is_self = context.account.id == account_id

    if not ((is_self and not data.real_name) or is_manager):
        raise exc.NoPermission

    # 先 update email 因為如果失敗就整個失敗
    if data.alternative_email is ...:
        pass
    elif data.alternative_email:  # 加或改 alternative email
        code = await db.account.add_email_verification(email=data.alternative_email, account_id=account_id)
        account = await db.account.read(account_id)
        await email.verification.send(to=data.alternative_email, code=code, username=account.username)
    else:  # 刪掉 alternative email
        await db.account.delete_alternative_email_by_id(account_id=account_id)

    await db.account.edit(account_id=account_id, username=data.username,
                          nickname=data.nickname, real_name=data.real_name)


@router.delete('/account/{account_id}')
@enveloped
async def delete_account(account_id: int) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    is_self = context.account.id == account_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await db.account.delete(account_id=account_id)


class DefaultStudentCardInput(BaseModel):
    student_card_id: int


@router.put('/account/{account_id}/default-student-card')
@enveloped
async def make_student_card_default(account_id: int, data: DefaultStudentCardInput) -> None:
    """
    ### 權限
    - System manager
    - Self
    """
    owner_id = await db.student_card.read_owner_id(student_card_id=data.student_card_id)
    if account_id != owner_id:
        raise exc.account.StudentCardDoesNotBelong

    is_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    is_self = context.account.id == owner_id

    if not (is_manager or is_self):
        raise exc.NoPermission

    await db.account.edit_default_student_card(account_id=account_id, student_card_id=data.student_card_id)


@router.get('/account/{account_id}/email-verification')
@enveloped
async def browse_all_account_pending_email_verification(account_id: int) \
        -> Sequence[do.EmailVerification]:
    """
    ### 權限
    - System manager
    - Self
    """
    if not (await service.rbac.validate_system(context.account.id, RoleType.manager)
            or context.account.id == account_id):
        raise exc.NoPermission

    email_verifications = await db.email_verification.browse(account_id=account_id)

    # issue 353: temp fix
    return [ev for ev in email_verifications if ev.student_id]
