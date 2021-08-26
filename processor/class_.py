from dataclasses import dataclass
from typing import Optional, Sequence, Union

from pydantic import BaseModel

from base import do, enum
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.email as email
import service
from util.api_doc import add_to_docstring

from .util import rbac, model


router = APIRouter(
    tags=['Class'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/class')
@enveloped
async def browse_class(request: Request) -> Sequence[do.Class]:
    """
    ### 權限
    - system normal: all
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await service.class_.browse()


@router.get('/class/{class_id}')
@enveloped
async def read_class(class_id: int, request: Request) -> do.Class:
    """
    ### 權限
    - System normal: all
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await service.class_.read(class_id=class_id)


class EditClassInput(BaseModel):
    name: str = None
    course_id: int = None


@router.patch('/class/{class_id}')
@enveloped
async def edit_class(class_id: int, data: EditClassInput, request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await service.class_.edit(
        class_id=class_id,
        name=data.name,
        course_id=data.course_id,
    )


@router.delete('/class/{class_id}')
@enveloped
async def delete_class(class_id: int, request: Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await service.class_.delete(class_id)


@dataclass
class BrowseClassMemberOutput:
    member_id: int
    role: enum.RoleType
    username: str
    real_name: str
    student_id: str
    institute_abbreviated_name: str


@router.get('/class/{class_id}/member')
@enveloped
async def browse_class_member(class_id: int, request: Request) -> Sequence[BrowseClassMemberOutput]:
    """
    ### 權限
    - Class normal
    - Class+ manager
    """
    if (not await rbac.validate(request.account.id, RoleType.normal, class_id=class_id)
            and not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)):
        raise exc.NoPermission

    results = await service.class_.browse_member_account_with_student_card_and_institute(class_id=class_id,
                                                                                         include_deleted=False)

    return [BrowseClassMemberOutput(member_id=member.member_id, role=member.role,
                                    username=account.username, real_name=account.real_name,
                                    student_id=student_card.student_id,
                                    institute_abbreviated_name=institute.abbreviated_name)
            for member, account, student_card, institute in results]


@dataclass
class ReadClassMemberOutput:
    member_id: Optional[int]
    member_referral: Optional[str]


@dataclass
class ReadClassMemberWithoutReferralOutput:
    member_id: Optional[int]


@router.get('/class/{class_id}/member/account-referral')
@enveloped
async def browse_class_member_with_account_referral(class_id: int, include_referral: bool, request: Request) \
        -> Union[Sequence[ReadClassMemberOutput], Sequence[ReadClassMemberWithoutReferralOutput]]:
    """
    ### 權限
    - Class normal
    - Class+ manager
    """
    if (not await rbac.validate(request.account.id, RoleType.normal, class_id=class_id)
            and not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)):
        raise exc.NoPermission

    results = await service.class_.browse_class_member_with_account_referral(class_id=class_id,
                                                                             include_deleted=False)
    return [ReadClassMemberOutput(member_id=member.member_id,
                                  member_referral=member_referral)
            for (member, member_referral) in results] if include_referral \
      else [ReadClassMemberWithoutReferralOutput(member_id=member.member_id)
            for (member, member_referral) in results]


class EditClassMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/class/{class_id}/member')
@enveloped
async def edit_class_member(class_id: int, data: Sequence[EditClassMemberInput], request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    for item in data:
        await service.class_.edit_member(class_id=class_id, member_id=item.member_id, role=item.role)

    updated_class_managers = [member.member_id for member in data if member.role is RoleType.manager]
    if updated_class_managers:
        class_manager_emails = await service.class_.browse_member_emails(class_id, RoleType.manager)
        await email.notification.notify_cm_change(class_manager_emails, updated_class_managers,
                                                  class_id, request.account.id)


class SetClassMemberInput(BaseModel):
    account_referral: str
    role: RoleType


@router.put('/class/{class_id}/member')
@enveloped
async def replace_class_members(class_id: int, data: Sequence[SetClassMemberInput], request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await service.class_.replace_members(class_id=class_id,
                                         member_roles=[(member.account_referral, member.role)
                                                       for member in data])

    updated_class_managers = [await service.account.referral_to_id(account_referral=member.account_referral)
                              for member in data if member.role is RoleType.manager]
    if updated_class_managers:
        class_manager_emails = await service.class_.browse_member_emails(class_id, RoleType.manager)
        await email.notification.notify_cm_change(class_manager_emails, updated_class_managers,
                                                  class_id, request.account.id)


@router.delete('/class/{class_id}/member/{member_id}')
@enveloped
async def delete_class_member(class_id: int, member_id: int, request: Request) -> None:
    """
    ### 權限
    - Class+ manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True):
        raise exc.NoPermission

    await service.class_.delete_member(class_id=class_id, member_id=member_id)


class AddTeamInput(BaseModel):
    name: str
    label: str


@router.post('/class/{class_id}/team', tags=['Team'])
@enveloped
async def add_team_under_class(class_id: int, data: AddTeamInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    team_id = await service.team.add(
        name=data.name,
        class_id=class_id,
        label=data.label,
    )

    return model.AddOutput(id=team_id)


@router.get('/class/{class_id}/team', tags=['Team'])
@enveloped
async def browse_team_under_class(class_id: int, request: Request) -> Sequence[do.Team]:
    """
    ### 權限
    - Class normal: all
    """
    class_role = await rbac.get_role(request.account.id, class_id=class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    return await service.team.browse(class_id=class_id)


@router.get('/class/{class_id}/submission', tags=['Submission'])
@enveloped
async def browse_submission_under_class(class_id: int, request: Request) -> Sequence[do.Submission]:
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    return await service.submission.browse_under_class(class_id=class_id)
