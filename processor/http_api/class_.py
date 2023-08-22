from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from pydantic import BaseModel

from base import do, enum, popo
from base.enum import RoleType, FilterOperator
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from persistence import email
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Class'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)

BROWSE_CLASS_COLUMNS = {
    'id': int,
    'name': str,
    'course_id': int,
    'is_deleted': bool,
}


class BrowseClassOutput(model.BrowseOutputBase):
    data: Sequence[do.Class]


@router.get('/class')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_COLUMNS.items()})
async def browse_class(
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseClassOutput:
    """
    ### 權限
    - system normal: all

    ### Available columns
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CLASS_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_COLUMNS)

    classes, total_count = await db.class_.browse_with_filter(limit=limit, offset=offset,
                                                              filters=filters, sorters=sorters)
    return BrowseClassOutput(classes, total_count=total_count)


@router.get('/class/{class_id}')
@enveloped
async def read_class(class_id: int) -> do.Class:
    """
    ### 權限
    - System normal: all
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.class_.read(class_id=class_id)


class EditClassInput(BaseModel):
    name: str = None
    course_id: int = None


@router.patch('/class/{class_id}')
@enveloped
async def edit_class(class_id: int, data: EditClassInput) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await service.rbac.validate_inherit(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await db.class_.edit(
        class_id=class_id,
        name=data.name,
        course_id=data.course_id,
    )


@router.delete('/class/{class_id}')
@enveloped
async def delete_class(class_id: int) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.class_.delete(class_id)


@dataclass
class ClassMemberData:
    member_id: int
    role: enum.RoleType
    username: str
    real_name: str
    student_id: str
    institute_abbreviated_name: str


BROWSE_CLASS_MEMBER_COLUMNS = {
    'member_id': int,
    'class_id': int,
    'role': enum.RoleType,
}


class BrowseClassMemberOutput(model.BrowseOutputBase):
    data: Sequence[ClassMemberData]


@router.get('/class/{class_id}/member')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_MEMBER_COLUMNS.items()})
async def browse_class_member(
        class_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseClassMemberOutput:
    """
    ### 權限
    - Class normal
    - Class+ manager

    ### Available columns
    """
    if (not await service.rbac.validate_class(context.account.id, RoleType.normal, class_id=class_id)
            and not await service.rbac.validate_inherit(context.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CLASS_MEMBER_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_MEMBER_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    result, total_count = await db.class_vo.browse_member_account_with_student_card_and_institute(
        limit=limit, offset=offset, filters=filters, sorters=sorters)
    data = [ClassMemberData(member_id=member.member_id, role=member.role,
                            username=account.username, real_name=account.real_name,
                            student_id=student_card.student_id,
                            institute_abbreviated_name=institute.abbreviated_name)
            for member, account, student_card, institute in result]
    return BrowseClassMemberOutput(data, total_count=total_count)


@dataclass
class ReadClassMemberOutput:
    member_id: Optional[int]
    member_referral: Optional[str]
    member_role: Optional[RoleType]


@router.get('/class/{class_id}/member/account-referral')
@enveloped
async def browse_all_class_member_with_account_referral(class_id: int) \
        -> Sequence[ReadClassMemberOutput]:
    """
    ### 權限
    - Class normal
    - Class+ manager
    """
    if (not await service.rbac.validate_class(context.account.id, RoleType.normal, class_id=class_id)
            and not await service.rbac.validate_inherit(context.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    results = await db.class_vo.browse_class_member_with_account_referral(class_id=class_id)
    return [ReadClassMemberOutput(member_id=member.member_id,
                                  member_referral=member_referral,
                                  member_role=member.role)
            for (member, member_referral) in results]


class SetClassMemberInput(BaseModel):
    account_referral: str
    role: RoleType


@router.put('/class/{class_id}/member')
@enveloped
async def replace_class_members(class_id: int, data: Sequence[SetClassMemberInput]) -> Sequence[bool]:
    """
    ### 權限
    - Class+ manager
    """
    if not await service.rbac.validate_inherit(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    member_roles = [(member.account_referral, member.role) for member in data]

    cm_before = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_before = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    result = await db.class_.replace_members(class_id=class_id, member_roles=member_roles)

    cm_after = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_after = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    if cm_before != cm_after:
        class_ = await db.class_.read(class_id=class_id)
        course = await db.course.read(course_id=class_.course_id)
        operator = await db.account.read(account_id=context.account.id)
        await email.notification.notify_cm_change(
            tos=(emails_after | emails_before),
            added_account_referrals=cm_after.difference(cm_before),
            removed_account_referrals=cm_before.difference(cm_after),
            class_name=class_.name,
            course_name=course.name,
            operator_name=operator.username,
        )

    return result


@router.delete('/class/{class_id}/member/{member_id}')
@enveloped
async def delete_class_member(class_id: int, member_id: int) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await db.class_.delete_member(class_id=class_id, member_id=member_id)


class AddTeamInput(BaseModel):
    name: str
    label: str


@router.post('/class/{class_id}/team', tags=['Team'])
@enveloped
async def add_team_under_class(class_id: int, data: AddTeamInput) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    team_id = await db.team.add(
        name=data.name,
        class_id=class_id,
        label=data.label,
    )

    return model.AddOutput(id=team_id)


BROWSE_TEAM_UNDER_CLASS_COLUMNS = {
    'id': int,
    'name': str,
    'class_id': int,
    'label': str,
    'is_deleted': bool,
}


class BrowseTeamUnderClassOutput(model.BrowseOutputBase):
    data: Sequence[do.Team]


@router.get('/class/{class_id}/team', tags=['Team'])
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_TEAM_UNDER_CLASS_COLUMNS.items()})
async def browse_team_under_class(
        class_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseTeamUnderClassOutput:
    """
    ### 權限
    - Class normal: all

    ### Available columns
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.normal, class_id=class_id):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_TEAM_UNDER_CLASS_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_TEAM_UNDER_CLASS_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))
    teams, total_count = await db.team.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)
    return BrowseTeamUnderClassOutput(teams, total_count=total_count)


BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS = {
    'id': int,
    'account_id': int,
    'problem_id': int,
    'language_id': int,
    'content_file_uuid': UUID,
    'content_length': int,
    'filename': str,
    'submit_time': model.ServerTZDatetime,
}


class BrowseSubmissionUnderClassOutput(model.BrowseOutputBase):
    data: Sequence[do.Submission]


@router.get('/class/{class_id}/submission', tags=['Submission'])
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS.items()})
async def browse_submission_under_class(
        class_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseSubmissionUnderClassOutput:
    """
    ### 權限
    - Class manager

    ### Available columns
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)

    submissions, total_count = await db.submission.browse_under_class(class_id=class_id,
                                                                      limit=limit, offset=offset,
                                                                      filters=filters, sorters=sorters)
    return BrowseSubmissionUnderClassOutput(submissions, total_count=total_count)
