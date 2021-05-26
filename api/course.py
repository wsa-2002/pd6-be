from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base.enum import CourseType, RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Course'],
    default_response_class=envelope.JSONResponse,
)


class CreateCourseInput(BaseModel):
    name: str
    type: CourseType
    is_enabled: bool
    is_hidden: bool


@dataclass
class CreateCourseOutput:
    id: int


@router.post('/course')
async def create_course(data: CreateCourseInput, request: auth.Request) -> CreateCourseOutput:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    course_id = await db.course.create(
        name=data.name,
        course_type=data.type,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )
    return CreateCourseOutput(id=course_id)


@router.get('/course')
async def get_courses(request: auth.Request) -> Sequence[db.course.do.Course]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    courses = await db.course.get_all(only_enabled=show_limited, exclude_hidden=show_limited)
    return courses


@router.get('/course/{course_id}')
async def get_course(course_id: int, request: auth.Request) -> db.course.do.Course:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    course = await db.course.get_by_id(course_id, only_enabled=show_limited, exclude_hidden=show_limited)
    return course


class EditCourseInput(BaseModel):
    name: Optional[str]
    type: Optional[CourseType]
    is_enabled: Optional[bool]
    is_hidden: Optional[bool]


@router.patch('/course/{course_id}')
async def edit_course(course_id: int, data: EditCourseInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.set_by_id(
        course_id=course_id,
        name=data.name,
        course_type=data.type,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )


@router.delete('/course/{course_id}')
async def remove_course(course_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.set_by_id(
        course_id=course_id,
        is_enabled=False,
    )


class CreateClassInput(BaseModel):
    name: str
    is_enabled: bool
    is_hidden: bool


@dataclass
class CreateClassOutput:
    id: int


@router.post('/course/{course_id}/class')
async def create_class_under_course(course_id: int, data: CreateClassInput, request: auth.Request) -> CreateClassOutput:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    class_id = await db.class_.create(
        name=data.name,
        course_id=course_id,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )

    return CreateClassOutput(id=class_id)


@router.get('/course/{course_id}/class')
async def get_classes_under_course(course_id: int, request: auth.Request) -> Sequence[int]:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.course.get_classes_id(course_id=course_id)


# TODO
# @router.get('/class')
# async def get_classes():
#     return [model.pbc109]


# TODO
# @router.get('/class/{class_id}')
# async def get_class(class_id: int):
#     return model.pbc109


# TODO
# @router.patch('/class/{class_id}')
# async def modify_class(class_id: int):
#     pass


# TODO
# @router.delete('/class/{class_id}')
# async def remove_class(class_id: int):
#     pass


# TODO
# @router.get('/class/{class_id}/member')
# async def get_class_members(class_id: int):
#     return [{
#         'account': model.account_simple,
#         'role': model.ta,
#     }]


# TODO
# @router.patch('/class/{class_id}/member')
# async def modify_class_member(class_id: int):
#     pass


# TODO
# @router.delete('/class/{class_id}/member')
# async def remove_class_member(class_id: int):
#     pass


# TODO
# @router.post('/class/{class_id}/team')
# async def create_team_under_class(class_id: int):
#     return {'id': 1}


# TODO
# @router.get('/class/{class_id}/team')
# async def get_teams_under_class(class_id: int):
#     return [model.team_1]


@router.get('/team')
async def get_teams(request: auth.Request) -> Sequence[db.team.do.Team]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    teams = await db.team.get_all(only_enabled=show_limited, exclude_hidden=show_limited)
    return teams


@router.get('/team/{team_id}')
async def get_team(team_id: int, request: auth.Request) -> db.team.do.Team:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    team = await db.team.get_by_id(team_id, only_enabled=show_limited, exclude_hidden=show_limited)
    return team


async def is_team_manager(team_id, account_id):
    # Check with team role
    try:
        req_account_role = await db.team.get_member_role(team_id=team_id, member_id=account_id)
    except exc.NotFound:  # Not even in team
        return False
    else:
        return req_account_role.is_manager


class ModifyTeamInput(BaseModel):
    name: str
    class_id: int
    is_enabled: bool
    is_hidden: bool


@router.patch('/team/{team_id}')
async def modify_team(team_id: int, data: ModifyTeamInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with team role
    if not await is_team_manager(team_id, request.account.id):
        raise exc.NoPermission

    await db.team.set_by_id(
        team_id=team_id,
        name=data.name,
        class_id=data.class_id,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )


@router.delete('/team/{team_id}')
async def remove_team(team_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with team role
    if not await is_team_manager(team_id, request.account.id):
        raise exc.NoPermission

    await db.team.set_by_id(
        team_id=team_id,
        is_enabled=False,
    )


@dataclass
class TeamMemberOutput:
    account_id: int
    role: RoleType


@router.get('/team/{team_id}/member')
async def get_team_members(team_id: int, request: auth.Request) -> Sequence[TeamMemberOutput]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    try:
        await db.team.get_member_role(team_id=team_id, member_id=request.account.id)
    except exc.NotFound:  # Not even in course
        if not request.account.role.is_manager:  # and is not manager
            raise exc.NoPermission

    member_roles = await db.team.get_member_ids(team_id=team_id)
    
    return [TeamMemberOutput(
        account_id=acc_id,
        role=role,
    ) for acc_id, role in member_roles]


class TeamMemberInput(BaseModel):
    member_id: int
    role: RoleType


@router.patch('/team/{team_id}/member')
async def modify_team_member(team_id: int, data: Sequence[TeamMemberInput], request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with team role
    if not await is_team_manager(team_id, request.account.id):
        raise exc.NoPermission

    for (member_id, role) in data:
        await db.team.set_member(team_id=team_id, member_id=member_id, role=role)


@router.delete('/team/{team_id}/member/{member_id}')
async def remove_team_member(team_id: int, member_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    await db.team.delete_member(team_id=team_id, member_id=member_id)
