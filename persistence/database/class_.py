from typing import Sequence, Collection, Tuple

from base.enum import RoleType

from . import do
from .base import SafeExecutor, SafeConnection


async def add(name: str, course_id: int, is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='add class',
            sql=r'INSERT INTO class'
                r'            (name, course_id, is_enabled, is_hidden)'
                r'     VALUES (%(name)s, %(course_id)s), %(is_enabled)s), %(is_hidden)s)'
                r'  RETURNING id',
            name=name,
            course_id=course_id,
            is_enabled=is_enabled,
            is_hidden=is_hidden,
            fetch=1,
    ) as (course_id,):
        return course_id


async def browse(course_id: int = None, only_enabled=True, exclude_hidden=True) -> Sequence[do.Class]:
    conditions = {}

    if course_id is not None:
        conditions['course_id'] = course_id
    if only_enabled:
        conditions['is_enabled'] = True
    if exclude_hidden:
        conditions['is_hidden'] = False

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='browse classes',
            sql=fr'SELECT id, name, course_id, is_enabled, is_hidden'
                fr'  FROM class'
                fr'{" WHERE " + cond_sql if cond_sql else ""}'
                fr' ORDER BY id',
            **conditions,
            fetch='all',
    ) as records:
        return [do.Class(id=id_, name=name, course_id=course_id, is_enabled=is_enabled, is_hidden=is_hidden)
                for (id_, name, course_id, is_enabled, is_hidden) in records]


async def read(class_id: int, only_enabled=True, exclude_hidden=True) -> do.Class:
    conditions = {}

    if only_enabled:
        conditions['is_enabled'] = True
    if exclude_hidden:
        conditions['is_hidden'] = False

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='read class by id',
            sql=fr'SELECT id, name, course_id, is_enabled, is_hidden'
                fr'  FROM class'
                fr' WHERE id = %(class_id)s'
                fr'{" AND " + cond_sql if cond_sql else ""}',
            class_id=class_id,
            **conditions,
            fetch=1,
    ) as (id_, name, course_id, is_enabled, is_hidden):
        return do.Class(id=id_, name=name, course_id=course_id, is_enabled=is_enabled, is_hidden=is_hidden)


async def edit(class_id: int,
               name: str = None, course_id: int = None, is_enabled: bool = None, is_hidden: bool = None):
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if course_id is not None:
        to_updates['course_id'] = course_id
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_enabled

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit class by id',
            sql=fr'UPDATE class'
                fr' WHERE class.id = %(class_id)s'
                fr'   SET {set_sql}',
            class_id=class_id,
            **to_updates,
    ):
        pass


# === member control


async def add_member(class_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='add member to class',
            sql=r'INSERT INTO class_member'
                r'            (class_id, member_id, role)'
                r'     VALUES (%(class_id)s, %(member_id)s), %(role)s))',
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


async def browse_members(class_id: int) -> Collection[Tuple[int, RoleType]]:
    async with SafeExecutor(
            event='browse class members',
            sql=r'SELECT account.id, class_member.role'
                r'  FROM class_member, account'
                r' WHERE class_member.member_id = account.id'
                r'   AND class_member.class_id = %(class_id)s',
            class_id=class_id,
            fetch='all',
    ) as results:
        return [(id_, RoleType(role_str)) for id_, role_str in results]


async def read_member_role(class_id: int, member_id: int) -> RoleType:
    async with SafeExecutor(
            event='read class member role',
            sql=r'SELECT role'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s and member_id = %(member_id)s',
            class_id=class_id,
            member_id=member_id,
            fetch=1,
    ) as (role,):
        return RoleType(role)


async def edit_member(class_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='set class member',
            sql=r'UPDATE class_member'
                r' WHERE class_id = %(class_id)s AND member_id = %(member_id)s'
                r'   SET role = %(role)s',
            class_id=class_id,
            member_id=member_id,
            role=role,
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


# === class -> team

async def browse_teams(class_id: int) -> Sequence[int]:
    async with SafeExecutor(
            event='get class teams',
            sql=r'SELECT team.id'
                r'  FROM team'
                r' WHERE team.class_id = %(class_id)s',
            class_id=class_id,
            fetch='all',
    ) as results:
        return [id_ for id_, in results]


# === class -> challenge

async def browse_challenges(class_id: int) -> Sequence[do.Challenge]:
    async with SafeExecutor(
            event='get challenges with class id',
            sql='SELECT id, type, name, setter_id, full_score, description, '
                '       start_time, end_time, is_enabled, is_hidden'
                '  FROM challenge'
                ' WHERE class_id = %(class_id)s',
            class_id=class_id,
            fetch='all',
    ) as results:
        return [do.Challenge(id=id_, class_id=class_id, type=type_, name=name, setter_id=setter_id,
                             description=description, start_time=start_time, end_time=end_time,
                             is_enabled=is_enabled, is_hidden=is_hidden)
                for id_, type_, name, setter_id, full_score, description, start_time, end_time, is_enabled, is_hidden
                in results]
