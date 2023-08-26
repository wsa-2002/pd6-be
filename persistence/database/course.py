from typing import Sequence

from base import do
from base.enum import CourseType

from . import class_
from .base import AutoTxConnection, FetchOne, FetchAll, OnlyExecute, ParamDict


async def add(name: str, course_type: CourseType) -> int:
    async with FetchOne(
            event='create course',
            sql=r'INSERT INTO course'
                r'            (name, type)'
                r'     VALUES (%(name)s, %(course_type)s)'
                r'  RETURNING id',
            name=name,
            course_type=course_type,
    ) as (course_id,):
        return course_id


async def browse(*, include_deleted=False) -> Sequence[do.Course]:
    conditions = []
    if not include_deleted:
        conditions.append("NOT is_deleted")

    cond_sql = ' AND '.join(conditions)

    async with FetchAll(
            event='get all courses',
            sql=fr'SELECT id, name, type, is_deleted'
                fr'  FROM course'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Course(id=id_, name=name, type=CourseType(c_type), is_deleted=is_deleted)
                for (id_, name, c_type, is_deleted) in records]


async def read(course_id: int, *, include_deleted=False) -> do.Course:
    async with FetchOne(
            event='get course by id',
            sql=fr'SELECT id, name, type, is_deleted'
                fr'  FROM course'
                fr' WHERE id = %(course_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            course_id=course_id,
    ) as (id_, name, c_type, is_deleted):
        return do.Course(id=id_, name=name, type=CourseType(c_type), is_deleted=is_deleted)


async def edit(course_id: int, name: str = None, course_type: CourseType = None):
    to_updates: ParamDict = {}

    if name is not None:
        to_updates['name'] = name
    if course_type is not None:
        to_updates['course_type'] = course_type

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='update course by id',
            sql=fr'UPDATE course'
                fr'   SET {set_sql}'
                fr' WHERE id = %(course_id)s',
            course_id=course_id,
            **to_updates,
    ):
        pass


async def delete(course_id: int) -> None:
    async with OnlyExecute(
            event='soft delete course',
            sql=r'UPDATE course'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(course_id)s',
            course_id=course_id,
            is_deleted=True,
    ):
        pass


async def delete_cascade(course_id: int) -> None:
    async with AutoTxConnection(event=f'cascade delete from course {course_id=}') as conn:
        await class_.delete_cascade_from_course(course_id=course_id, cascading_conn=conn)

        await conn.execute(r'UPDATE course'
                           r'   SET is_deleted = $1'
                           r' WHERE id = $2',
                           True, course_id)
