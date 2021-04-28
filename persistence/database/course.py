from typing import Sequence, Collection

from base.enum import CourseType, RoleType

from . import do
from .base import SafeExecutor, SafeConnection


async def create(name: str, course_type: CourseType, is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='create course',
            sql=r'INSERT INTO course'
                r'            (name, type, is_enabled, is_hidden)'
                r'     VALUES (%(name)s, %(course_type)s), %(is_enabled)s), %(is_hidden)s)'
                r'  RETURNING id',
            name=name,
            course_type=course_type,
            is_enabled=is_enabled,
            is_hidden=is_hidden,
            fetch=1,
    ) as (course_id,):
        return course_id


async def get_all(only_enabled=True, exclude_hidden=True) -> Sequence[do.Course]:
    conditions = []
    if only_enabled:
        conditions.append('is_enabled = TRUE')
    if exclude_hidden:
        conditions.append('is_hidden = FALSE')
    cond_sql = ' AND '.join(conditions)

    async with SafeExecutor(
            event='get all courses',
            sql=fr'SELECT id, name, type, is_enabled, is_hidden'
                fr'  FROM course'
                fr'{" WHERE " + cond_sql if cond_sql else ""}'
                fr' ORDER BY id',
            fetch='all',
    ) as records:
        return [do.Course(id=id_, name=name, type=CourseType.from_str(c_type),
                          is_enabled=is_enabled, is_hidden=is_hidden)
                for (id_, name, c_type, is_enabled, is_hidden) in records]


async def get_by_id(course_id: int, only_enabled=True, exclude_hidden=True) -> do.Course:
    conditions = []
    if only_enabled:
        conditions.append('is_enabled = TRUE')
    if exclude_hidden:
        conditions.append('is_hidden = FALSE')
    cond_sql = ' AND '.join(conditions)

    async with SafeExecutor(
            event='get course by id',
            sql=fr'SELECT id, name, type, is_enabled, is_hidden'
                fr'  FROM course'
                fr' WHERE id = %(course_id)s'
                fr'{" AND " + cond_sql if cond_sql else ""}',
            course_id=course_id,
            fetch=1,
    ) as (id_, name, c_type, is_enabled, is_hidden):
        return do.Course(id=id_, name=name, type=CourseType.from_str(c_type),
                         is_enabled=is_enabled, is_hidden=is_hidden)


async def set_by_id(course_id: int,
                    name: str = None, course_type: CourseType = None, is_enabled: bool = None, is_hidden: bool = None):
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if course_type is not None:
        to_updates['course_type'] = course_type
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_enabled

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update course by id',
            sql=fr'UPDATE course'
                fr' WHERE course.id = %(course_id)s'
                fr'   SET {set_sql}',
            course_id=course_id,
            **to_updates,
    ):
        pass


# === member control


async def add_member(course_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='add member to course',
            sql=r'INSERT INTO course_member'
                r'            (course_id, member_id, role)'
                r'     VALUES (%(course_id)s, %(member_id)s), %(role)s))',
            course_id=course_id,
            member_id=member_id,
            role=role,
    ):
        pass


async def add_members(course_id: int, member_roles: Collection[Sequence[int, RoleType]]):
    async with SafeConnection(event='add members to course') as conn:
        await conn.executemany(
            command=r'INSERT INTO course_member'
                    r'            (course_id, member_id, role)'
                    r'     VALUES ($1, $2, $3)',
            args=[(course_id, member_id, role)
                  for member_id, role in member_roles],
        )


async def get_member_ids(course_id: int) -> Collection[Sequence[int, RoleType]]:
    async with SafeExecutor(
            event='get course members id',
            sql='SELECT account.id, course_member.role'
                '  FROM course_member, account'
                ' WHERE course_member.member_id = account.id'
                '   AND course_member.course_id = %(course_id)s',
            course_id=course_id,
            fetch='all',
    ) as results:
        return [(id_, RoleType.from_str(role_str)) for id_, role_str in results]


async def get_member_role(course_id: int, member_id: int) -> RoleType:
    async with SafeExecutor(
            event='get course member role',
            sql=r'SELECT role'
                r'  FROM course_member'
                r' WHERE course_id = %(course_id)s and member_id = %(member_id)s',
            course_id=course_id,
            member_id=member_id,
            fetch=1,
    ) as (role,):
        return RoleType.from_str(role)


async def set_member(course_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='set course member',
            sql=r'UPDATE course_member'
                r' WHERE course_id = %(course_id)s AND member_id = %(member_id)s'
                r'   SET role = %(role)s',
            course_id=course_id,
            member_id=member_id,
            role=role,
    ):
        pass


async def delete_member(course_id: int, member_id: int):
    async with SafeExecutor(
            event='HARD DELETE course member',
            sql=r'DELETE FROM course_member'
                r'      WHERE course_id = %(course_id)s AND member_id = %(member_id)s',
            course_id=course_id,
            member_id=member_id,
    ):
        pass


# === course -> class

async def get_classes_id(course_id: int) -> Collection[int]:
    async with SafeExecutor(
            event='get course classes',
            sql=r'SELECT class.id'
                r'  FROM class'
                r' WHERE class.course_id = %(course_id)s',
            course_id=course_id,
            fetch='all',
    ) as results:
        return [id_ for id_, in results]
