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


@router.post('/course/{course_id}/class', tags=['Class'])
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


@router.get('/course/{course_id}/class', tags=['Class'])
async def get_classes_under_course(course_id: int, request: auth.Request) -> Sequence[int]:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.course.get_classes_id(course_id=course_id)
