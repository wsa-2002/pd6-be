from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import CourseType, RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Course'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


class AddCourseInput(BaseModel):
    name: str
    type: CourseType


@dataclass
class AddCourseOutput:
    id: int


@router.post('/course')
@enveloped
async def add_course(data: AddCourseInput, request: auth.Request) -> AddCourseOutput:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    course_id = await db.course.add(
        name=data.name,
        course_type=data.type,
    )
    return AddCourseOutput(id=course_id)


@router.get('/course')
@enveloped
async def browse_course(request: auth.Request) -> Sequence[do.Course]:
    """
    ### 權限
    - System manager (hidden)
    - System normal (not hidden)
    """
    system_role = await rbac.get_role(request.account.id)
    if system_role < RoleType.normal:
        raise exc.NoPermission

    courses = await db.course.browse()
    return courses


@router.get('/course/{course_id}')
@enveloped
async def read_course(course_id: int, request: auth.Request) -> do.Course:
    """
    ### 權限
    - System manager (hidden)
    - System normal (not hidden)
    """
    system_role = await rbac.get_role(request.account.id)
    if system_role < RoleType.normal:
        raise exc.NoPermission

    course = await db.course.read(course_id)
    return course


class EditCourseInput(BaseModel):
    name: str = None
    type: CourseType = None
    is_hidden: bool = None


@router.patch('/course/{course_id}')
@enveloped
async def edit_course(course_id: int, data: EditCourseInput, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.edit(
        course_id=course_id,
        name=data.name,
        course_type=data.type,
    )


@router.delete('/course/{course_id}')
@enveloped
async def delete_course(course_id: int, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.delete(course_id)


class AddClassInput(BaseModel):
    name: str


@dataclass
class AddClassOutput:
    id: int


@router.post('/course/{course_id}/class', tags=['Class'])
@enveloped
async def add_class_under_course(course_id: int, data: AddClassInput, request: auth.Request) -> AddClassOutput:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    class_id = await db.class_.add(
        name=data.name,
        course_id=course_id,
    )

    return AddClassOutput(id=class_id)


@router.get('/course/{course_id}/class', tags=['Class'])
@enveloped
async def browse_class_under_course(course_id: int, request: auth.Request) -> Sequence[do.Class]:
    """
    ### 權限
    - Class+ manager (hidden)
    - System normal (not hidden)
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # FIXME
    # 先包含 hidden，再篩選這個 account 能看到的 class
    return db.class_.browse(course_id=course_id)
