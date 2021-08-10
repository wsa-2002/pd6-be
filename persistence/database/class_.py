from typing import Sequence, Collection, Tuple

from base import do
from base.enum import RoleType

from . import team, challenge
from .base import SafeExecutor, SafeConnection


async def add(name: str, course_id: int) -> int:
    async with SafeExecutor(
            event='add class',
            sql=r'INSERT INTO class'
                r'            (name, course_id)'
                r'     VALUES (%(name)s, %(course_id)s)'
                r'  RETURNING id',
            name=name,
            course_id=course_id,
            fetch=1,
    ) as (course_id,):
        return course_id


async def browse(course_id: int = None, include_deleted=False) -> Sequence[do.Class]:
    conditions = {}
    if course_id is not None:
        conditions['course_id'] = course_id

    filters = []
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(list(fr"{field_name} = %({field_name})s" for field_name in conditions)
                            + filters)

    async with SafeExecutor(
            event='browse classes',
            sql=fr'SELECT id, name, course_id, is_deleted'
                fr'  FROM class'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY course_id ASC, id ASC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.Class(id=id_, name=name, course_id=course_id, is_deleted=is_deleted)
                for (id_, name, course_id, is_deleted) in records]


async def browse_from_member_role(member_id: int, role: RoleType, include_deleted=False) \
        -> Sequence[do.Class]:
    async with SafeExecutor(
            event='browse classes from account role',
            sql=fr'SELECT class.id, class.name, class.course_id, class.is_deleted'
                fr'  FROM class'
                fr'       INNER JOIN class_member'
                fr'               ON class_member.class_id = class.id'
                fr'              AND class_member.member_id = %(member_id)s'
                fr' WHERE class_member.role = %(role)s'
                fr'{" AND NOT class.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY class.course_id ASC, class.id ASC',
            role=role,
            member_id=member_id,
            fetch='all',
    ) as records:
        return [do.Class(id=id_, name=name, course_id=course_id, is_deleted=is_deleted)
                for (id_, name, course_id, is_deleted) in records]


async def read(class_id: int, *, include_deleted=False) -> do.Class:
    async with SafeExecutor(
            event='read class by id',
            sql=fr'SELECT id, name, course_id, is_deleted'
                fr'  FROM class'
                fr' WHERE id = %(class_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            class_id=class_id,
            fetch=1,
    ) as (id_, name, course_id, is_deleted):
        return do.Class(id=id_, name=name, course_id=course_id, is_deleted=is_deleted)


async def edit(class_id: int, name: str = None, course_id: int = None):
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if course_id is not None:
        to_updates['course_id'] = course_id

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


async def delete_cascade(class_id: int) -> None:
    async with SafeConnection(event=f'cascade delete from class {class_id=}') as conn:
        async with conn.transaction():
            await team.delete_cascade_from_class(class_id=class_id, cascading_conn=conn)
            await challenge.delete_cascade_from_class(class_id=class_id, cascading_conn=conn)

            await conn.execute(fr'UPDATE class'
                               fr'   SET is_deleted = $1'
                               fr' WHERE id = $2',
                               True, class_id)


async def delete_cascade_from_course(course_id: int, cascading_conn=None) -> None:
    if cascading_conn:
        await _delete_cascade_from_course(course_id, conn=cascading_conn)
        return

    async with SafeConnection(event=f'cascade delete class from course {course_id=}') as conn:
        async with conn.transaction():
            await _delete_cascade_from_course(course_id, conn=conn)


async def _delete_cascade_from_course(course_id: int, conn) -> None:
    await conn.execute(r'UPDATE class'
                       r'   SET is_deleted = $1'
                       r' WHERE course_id = $2',
                       True, course_id)


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


async def browse_role_by_account_id(account_id: int) -> Sequence[do.ClassMember]:
    async with SafeExecutor(
            event='browse class role by account_id',
            sql=fr'SELECT class_id, member_id, role'
                fr'  FROM class_member'
                fr' WHERE member_id = %(account_id)s',
            account_id=account_id,
            fetch='all',
    ) as records:
        return [do.ClassMember(class_id=class_id, member_id=member_id, role=RoleType(role))
                for (class_id, member_id, role) in records]


async def browse_members(class_id: int) -> Sequence[do.ClassMember]:
    async with SafeExecutor(
            event='browse class members',
            sql=r'SELECT account.id, class_member.class_id, class_member.role'
                r'  FROM class_member, account'
                r' WHERE class_member.member_id = account.id'
                r'   AND class_member.class_id = %(class_id)s'
                r' ORDER BY class_member.role DESC, account.id ASC',
            class_id=class_id,
            fetch='all',
    ) as records:
        return [do.ClassMember(member_id=id_, class_id=class_id, role=RoleType(role_str))
                for id_, class_id, role_str in records]


async def read_member(class_id: int, member_id: int) -> do.ClassMember:
    async with SafeExecutor(
            event='read class member role',
            sql=r'SELECT member_id, class_id, role'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s and member_id = %(member_id)s',
            class_id=class_id,
            member_id=member_id,
            fetch=1,
    ) as (member_id, class_id, role):
        return do.ClassMember(member_id=member_id, class_id=class_id, role=RoleType(role))


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
    conditions = {}
    if role is not None:
        conditions['role'] = role

    async with SafeExecutor(
            event='browse class member emails',
            sql=fr'SELECT student_card.email'
                fr'  FROM class_member, student_card'
                fr' WHERE class_member.member_id = student_card.account_id'
                fr'   AND student_card.is_default = true'
                fr'   AND class_member.class_id = %(class_id)s'
                fr' {"AND class_member.role = %(role)s" if role is not None else ""}',
            class_id=class_id,
            **conditions,
            fetch='all',
    ) as records:
        return [institute_email for institute_email, in records]
