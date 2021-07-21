from typing import Sequence, Collection, Tuple

import log
from base import do
from base.enum import RoleType

from .base import SafeExecutor, SafeConnection


async def add(name: str, course_id: int, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='add class',
            sql=r'INSERT INTO class'
                r'            (name, course_id, is_hidden)'
                r'     VALUES (%(name)s, %(course_id)s, %(is_hidden)s)'
                r'  RETURNING id',
            name=name,
            course_id=course_id,
            is_hidden=is_hidden,
            fetch=1,
    ) as (course_id,):
        return course_id


async def browse(course_id: int = None, include_hidden=False, include_deleted=False) -> Sequence[do.Class]:
    conditions = {}
    if course_id is not None:
        conditions['course_id'] = course_id

    filters = []
    if not include_hidden:
        filters.append("NOT is_hidden")
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(list(fr"{field_name} = %({field_name})s" for field_name in conditions)
                            + filters)

    async with SafeExecutor(
            event='browse classes',
            sql=fr'SELECT id, name, course_id, is_hidden, is_deleted'
                fr'  FROM class'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY course_id ASC, id ASC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.Class(id=id_, name=name, course_id=course_id, is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, name, course_id, is_hidden, is_deleted) in records]


async def browse_from_member_role(member_id: int, role: RoleType, include_hidden=False, include_deleted=False) \
        -> Sequence[do.Class]:
    async with SafeExecutor(
            event='browse classes from account role',
            sql=fr'SELECT class.id, class.name, class.course_id, class.is_hidden, class.is_deleted'
                fr'  FROM class'
                fr'       INNER JOIN class_member'
                fr'               ON class_member.class_id = class.id'
                fr'              AND class_member.member_id = %(member_id)s'
                fr' WHERE class_member.role = %(role)s'
                fr'{" AND NOT class.is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT class.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY class.course_id ASC, class.id ASC',
            role=role,
            member_id=member_id,
            fetch='all',
    ) as records:
        return [do.Class(id=id_, name=name, course_id=course_id, is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, name, course_id, is_hidden, is_deleted) in records]


async def read(class_id: int, *, include_hidden=False, include_deleted=False) -> do.Class:
    async with SafeExecutor(
            event='read class by id',
            sql=fr'SELECT id, name, course_id, is_hidden, is_deleted'
                fr'  FROM class'
                fr' WHERE id = %(class_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            class_id=class_id,
            fetch=1,
    ) as (id_, name, course_id, is_hidden, is_deleted):
        return do.Class(id=id_, name=name, course_id=course_id, is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(class_id: int,
               name: str = None, course_id: int = None, is_hidden: bool = None):
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if course_id is not None:
        to_updates['course_id'] = course_id
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit class by id',
            sql=fr'UPDATE class'
                fr'   SET {set_sql}'
                fr' WHERE id = %(class_id)s',
            class_id=class_id,
            **to_updates,
    ):
        pass


async def delete(class_id: int) -> None:
    async with SafeExecutor(
            event='soft delete class',
            sql=fr'UPDATE class'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(class_id)s',
            class_id=class_id,
            is_deleted=True,
    ):
        pass


# === member control


async def add_member(class_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='add member to class',
            sql=r'INSERT INTO class_member'
                r'            (class_id, member_id, role)'
                r'     VALUES (%(class_id)s, %(member_id)s, %(role)s)',
            class_id=class_id,
            member_id=member_id,
            role=role,
    ):
        pass


async def add_members(class_id: int, member_roles: Collection[Tuple[int, RoleType]]):
    async with SafeConnection(event='add members to class') as conn:
        await conn.executemany(
            command=r'INSERT INTO class_member'
                    r'            (class_id, member_id, role)'
                    r'     VALUES ($1, $2, $3)',
            args=[(class_id, member_id, role)
                  for member_id, role in member_roles],
        )


async def browse_members(class_id: int) -> Sequence[do.Member]:
    async with SafeExecutor(
            event='browse class members',
            sql=r'SELECT account.id, class_member.role'
                r'  FROM class_member, account'
                r' WHERE class_member.member_id = account.id'
                r'   AND class_member.class_id = %(class_id)s'
                r' ORDER BY class_member.role DESC, account.id ASC',
            class_id=class_id,
            fetch='all',
    ) as records:
        return [do.Member(member_id=id_, role=RoleType(role_str)) for id_, role_str in records]


async def read_member(class_id: int, member_id: int) -> do.Member:
    async with SafeExecutor(
            event='read class member role',
            sql=r'SELECT role'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s and member_id = %(member_id)s',
            class_id=class_id,
            member_id=member_id,
            fetch=1,
    ) as (role,):
        return do.Member(member_id=member_id, role=RoleType(role))


async def edit_member(class_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='set class member',
            sql=r'UPDATE class_member'
                r'   SET role = %(role)s'
                r' WHERE class_id = %(class_id)s AND member_id = %(member_id)s',
            role=role,
            class_id=class_id,
            member_id=member_id,
    ):
        pass


async def delete_member(class_id: int, member_id: int):
    async with SafeExecutor(
            event='HARD DELETE class member',
            sql=r'DELETE FROM class_member'
                r'      WHERE class_id = %(class_id)s AND member_id = %(member_id)s',
            class_id=class_id,
            member_id=member_id,
    ):
        pass


async def browse_member_emails(class_id: int, role: RoleType = None) -> Sequence[str]:
    conditions = {
        'class_id': class_id
    }
    if role is not None:
        conditions['role'] = role

    async with SafeExecutor(
            event='browse class member emails',
            sql=fr'SELECT student_card.email'
                fr'  FROM class_member, student_card'
                fr' WHERE class_member.member_id = student_card.account_id'
                fr'   AND student_card.is_default = true'
                fr'   AND class_member.class_id = %(class_id)s'
                fr'   {"AND class_member.role = %(role)s" if role is not None else ""}',
            **conditions,
            fetch='all',
    ) as records:
        return [institute_email for institute_email, in records]
