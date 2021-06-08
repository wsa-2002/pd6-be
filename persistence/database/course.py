from typing import Sequence, Collection, Tuple

from base import do
from base.enum import CourseType, RoleType

from .base import SafeExecutor, SafeConnection


async def add(name: str, course_type: CourseType, is_hidden: bool, is_deleted: bool) -> int:
    async with SafeExecutor(
            event='create course',
            sql=r'INSERT INTO course'
                r'            (name, type, is_hidden, is_deleted)'
                r'     VALUES (%(name)s, %(course_type)s), %(is_hidden)s), %(is_deleted)s)'
                r'  RETURNING id',
            name=name,
            course_type=course_type,
            is_hidden=is_hidden,
            is_deleted=is_deleted,
            fetch=1,
    ) as (course_id,):
        return course_id


async def browse(*, include_hidden=False, include_deleted=False) -> Sequence[do.Course]:
    conditions = []
    if not include_hidden:
        conditions.append("NOT is_hidden")
    if not include_deleted:
        conditions.append("NOT is_deleted")

    cond_sql = ' AND '.join(conditions)

    async with SafeExecutor(
            event='get all courses',
            sql=fr'SELECT id, name, type, is_hidden, is_hidden'
                fr'  FROM course'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.Course(id=id_, name=name, type=CourseType(c_type),
                          is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, name, c_type, is_hidden, is_deleted) in records]


async def read(course_id: int, *, include_hidden=False, include_deleted=False) -> do.Course:
    async with SafeExecutor(
            event='get course by id',
            sql=fr'SELECT id, name, type, is_hidden, is_deleted'
                fr'  FROM course'
                fr' WHERE id = %(course_id)s'
                fr'{" AND NOT is_hidden" if include_hidden else ""}'
                fr'{" AND NOT is_deleted" if include_deleted else ""}',
            course_id=course_id,
            fetch=1,
    ) as (id_, name, c_type, is_hidden, is_deleted):
        return do.Course(id=id_, name=name, type=CourseType(c_type),
                         is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(course_id: int,
               name: str = None, course_type: CourseType = None, is_hidden: bool = None):
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if course_type is not None:
        to_updates['course_type'] = course_type
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update course by id',
            sql=fr'UPDATE course'
                fr'   SET {set_sql}'
                fr' WHERE id = %(course_id)s',
            course_id=course_id,
            **to_updates,
    ):
        pass


async def delete(course_id: int) -> None:
    async with SafeExecutor(
            event='soft delete course',
            sql=fr'UPDATE course'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(course_id)s',
            course_id=course_id,
            is_deleted=True,
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


async def add_members(course_id: int, member_roles: Collection[Tuple[int, RoleType]]):
    async with SafeConnection(event='add members to course') as conn:
        await conn.executemany(
            command=r'INSERT INTO course_member'
                    r'            (course_id, member_id, role)'
                    r'     VALUES ($1, $2, $3)',
            args=[(course_id, member_id, role)
                  for member_id, role in member_roles],
        )


async def browse_members(course_id: int) -> Sequence[do.Member]:
    async with SafeExecutor(
            event='get course members id',
            sql=r'SELECT account.id, course_member.role'
                r'  FROM course_member, account'
                r' WHERE course_member.member_id = account.id'
                r'   AND course_member.course_id = %(course_id)s'
                r' ORDER BY course_member.role DESC, account.id ASC',
            course_id=course_id,
            fetch='all',
    ) as records:
        return [do.Member(member_id=id_, role=RoleType(role_str)) for id_, role_str in records]


async def read_member(course_id: int, member_id: int) -> do.Member:
    async with SafeExecutor(
            event='get course member role',
            sql=r'SELECT role'
                r'  FROM course_member'
                r' WHERE course_id = %(course_id)s and member_id = %(member_id)s',
            course_id=course_id,
            member_id=member_id,
            fetch=1,
    ) as (role,):
        return do.Member(member_id=member_id, role=RoleType(role))


async def edit_member(course_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='set course member',
            sql=r'UPDATE course_member'
                r'   SET role = %(role)s'
                r' WHERE course_id = %(course_id)s AND member_id = %(member_id)s',
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
