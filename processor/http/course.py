from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import CourseType, RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import service
from util import model

router = APIRouter(
    tags=['Course'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddCourseInput(BaseModel):
    name: str
    type: CourseType


@router.post('/course')
@enveloped
async def add_course(data: AddCourseInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    course_id = await db.course.add(
        name=data.name,
        course_type=data.type,
    )
    return model.AddOutput(id=course_id)


@router.get('/course')
@enveloped
async def browse_all_course(request: Request) -> Sequence[do.Course]:
    """
    ### 權限
    - System manager (hidden)
    - System normal (not hidden)
    """
    system_role = await service.rbac.get_role(request.account.id)
    if system_role < RoleType.normal:
        raise exc.NoPermission

    courses = await db.course.browse()
    return courses


@router.get('/course/{course_id}')
@enveloped
async def read_course(course_id: int, request: Request) -> do.Course:
    """
    ### 權限
    - System manager (hidden)
    - System normal (not hidden)
    """
    system_role = await service.rbac.get_role(request.account.id)
    if system_role < RoleType.normal:
        raise exc.NoPermission

    course = await db.course.read(course_id)
    return course


class EditCourseInput(BaseModel):
    name: str = None
    type: CourseType = None


@router.patch('/course/{course_id}')
@enveloped
async def edit_course(course_id: int, data: EditCourseInput, request: Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.edit(
        course_id=course_id,
        name=data.name,
        course_type=data.type,
    )


@router.delete('/course/{course_id}')
@enveloped
async def delete_course(course_id: int, request: Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.delete(course_id)


class AddClassInput(BaseModel):
    name: str


@router.post('/course/{course_id}/class', tags=['Class'])
@enveloped
async def add_class_under_course(course_id: int, data: AddClassInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    class_id = await db.class_.add(
        name=data.name,
        course_id=course_id,
    )

    return model.AddOutput(id=class_id)


@router.get('/course/{course_id}/class', tags=['Class'])
@enveloped
async def browse_all_class_under_course(course_id: int, request: Request) -> Sequence[do.Class]:
    """
    ### 權限
    - Class+ manager (hidden)
    - System normal (not hidden)
    """
    if not await service.rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.class_.browse(course_id=course_id)
