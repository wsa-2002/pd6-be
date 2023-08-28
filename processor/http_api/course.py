from dataclasses import dataclass
from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import CourseType, RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from util import model
from util.context import context

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
async def add_course(data: AddCourseInput) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    course_id = await db.course.add(
        name=data.name,
        course_type=data.type,
    )
    return model.AddOutput(id=course_id)


@router.get('/course')
@enveloped
async def browse_all_course() -> Sequence[do.Course]:
    """
    ### 權限
    - System normal
    """
    system_role = await service.rbac.get_system_role(context.account.id)
    if system_role < RoleType.normal:
        raise exc.NoPermission

    courses = await db.course.browse()
    return courses


@router.get('/course/{course_id}')
@enveloped
async def read_course(course_id: int) -> do.Course:
    """
    ### 權限
    - System normal
    """
    system_role = await service.rbac.get_system_role(context.account.id)
    if system_role < RoleType.normal:
        raise exc.NoPermission

    course = await db.course.read(course_id)
    return course


class EditCourseInput(BaseModel):
    name: str = None
    type: CourseType = None


@router.patch('/course/{course_id}')
@enveloped
async def edit_course(course_id: int, data: EditCourseInput) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.edit(
        course_id=course_id,
        name=data.name,
        course_type=data.type,
    )


@router.delete('/course/{course_id}')
@enveloped
async def delete_course(course_id: int) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    await db.course.delete(course_id)


class AddClassInput(BaseModel):
    name: str


@router.post('/course/{course_id}/class', tags=['Class'])
@enveloped
async def add_class_under_course(course_id: int, data: AddClassInput) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    class_id = await db.class_.add(
        name=data.name,
        course_id=course_id,
    )

    return model.AddOutput(id=class_id)


@dataclass
class BrowseAllClassUnderCourseOutput:
    class_info: do.Class
    member_count: int


@router.get('/course/{course_id}/class', tags=['Class'])
@enveloped
async def browse_all_class_under_course(course_id: int) -> Sequence[BrowseAllClassUnderCourseOutput]:
    """
    ### 權限
    - System normal
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    classes = await db.class_.browse(course_id=course_id)
    if not classes:
        return []

    member_counts = await db.class_.get_member_counts([class_.id for class_ in classes])

    return [BrowseAllClassUnderCourseOutput(class_, count) for class_, count in zip(classes, member_counts)]
