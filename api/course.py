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


class AddCourseInput(BaseModel):
    name: str
    type: CourseType
    is_enabled: bool
    is_hidden: bool


@dataclass
class AddCourseOutput:
    id: int


@router.post('/course')
async def add_course(data: AddCourseInput, request: auth.Request) -> AddCourseOutput:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    course_id = await db.course.add(
        name=data.name,
        course_type=data.type,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )
    return AddCourseOutput(id=course_id)


@router.get('/course')
async def browse_courses(request: auth.Request) -> Sequence[db.course.do.Course]:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    courses = await db.course.browse(only_enabled=show_limited, exclude_hidden=show_limited)
    return courses


@router.get('/course/{course_id}')
async def read_course(course_id: int, request: auth.Request) -> db.course.do.Course:
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    show_limited = request.account.role.not_manager
    course = await db.course.read(course_id, only_enabled=show_limited, exclude_hidden=show_limited)
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

    await db.course.edit(
        course_id=course_id,
        name=data.name,
        course_type=data.type,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )


@router.delete('/course/{course_id}')
async def delete_course(course_id: int, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.edit(
        course_id=course_id,
        is_enabled=False,
    )


class AddClassInput(BaseModel):
    name: str
    is_enabled: bool
    is_hidden: bool


@dataclass
class AddClassOutput:
    id: int


@router.post('/course/{course_id}/class', tags=['Class'])
async def add_class_under_course(course_id: int, data: AddClassInput, request: auth.Request) -> AddClassOutput:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    class_id = await db.class_.add(
        name=data.name,
        course_id=course_id,
        is_enabled=data.is_enabled,
        is_hidden=data.is_hidden,
    )

    return AddClassOutput(id=class_id)


@router.get('/course/{course_id}/class', tags=['Class'])
async def browse_classes_under_course(course_id: int, request: auth.Request) -> Sequence[int]:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.course.browse_classes(course_id=course_id)
