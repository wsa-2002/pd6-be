from typing import Tuple, Collection, Sequence

from base import do
from base.enum import RoleType

from .base import SafeExecutor


async def add(name: str, class_id: int, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='add team',
            sql=r'INSERT INTO team'
                r'            (name, type, is_hidden)'
                r'     VALUES (%(name)s, %(class_id)s), %(is_hidden)s))'
                r'  RETURNING id',
            name=name,
            class_id=class_id,
            is_hidden=is_hidden,
            fetch=1,
    ) as (class_id,):
        return class_id


async def browse(class_id: int = None, include_hidden=False, include_deleted=False) -> Sequence[do.Team]:
    conditions = {}
    if class_id is not None:
        conditions['class_id'] = class_id

    filters = []
    if not include_hidden:
        filters.append("NOT is_hidden")
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(list(fr"{field_name} = %({field_name})s" for field_name in conditions)
                            + filters)

    async with SafeExecutor(
            event='browse teams',
            sql=fr'SELECT id, name, class_id, is_hidden, is_deleted'
                fr'  FROM team'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY class_id ASC, id ASC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.Team(id=id_, name=name, class_id=class_id, is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, name, class_id, is_hidden, is_deleted) in records]


async def read(team_id: int, *, include_hidden=False, include_deleted=False) -> do.Team:
    async with SafeExecutor(
            event='get team by id',
            sql=fr'SELECT id, name, class_id, is_hidden, is_deleted'
                fr'  FROM team'
                fr' WHERE id = %(team_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            team_id=team_id,
            fetch=1,
    ) as (id_, name, class_id, is_hidden, is_deleted):
        return do.Team(id=id_, name=name, class_id=class_id, is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(team_id: int,
               name: str = None, class_id: int = None, is_hidden: bool = None):
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if class_id is not None:
        to_updates['class_id'] = class_id
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update team by id',
            sql=fr'UPDATE team'
                fr'   SET {set_sql}'
                fr' WHERE id = %(team_id)s',
            team_id=team_id,
            **to_updates,
    ):
        pass


async def delete(team_id: int) -> None:
    async with SafeExecutor(
            event='soft delete team',
            sql=fr'UPDATE team'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(team_id)s',
            team_id=team_id,
            is_deleted=True,
    ):
        pass


# === member control


async def browse_members(team_id: int) -> Sequence[do.Member]:
    async with SafeExecutor(
            event='get team members id',
            sql=r'SELECT account.id, team_member.role'
                r'  FROM team_member, account'
                r' WHERE team_member.member_id = account.id'
                r'   AND team_member.team_id = %(team_id)s'
                r' ORDER BY team_member.role DESC, account.id ASC',
            team_id=team_id,
            fetch='all',
    ) as records:
        return [do.Member(member_id=id_, role=RoleType(role_str)) for id_, role_str in records]


async def read_member(team_id: int, member_id: int) -> do.Member:
    async with SafeExecutor(
            event='get team member role',
            sql=r'SELECT role'
                r'  FROM team_member'
                r' WHERE team_id = %(team_id)s and member_id = %(member_id)s',
            team_id=team_id,
            member_id=member_id,
            fetch=1,
    ) as (role,):
        return do.Member(member_id=member_id, role=RoleType(role))


async def edit_member(team_id: int, member_id: int, role: RoleType):
    async with SafeExecutor(
            event='set team member',
            sql=r'UPDATE team_member'
                r'   SET role = %(role)s'
                r' WHERE team_id = %(team_id)s AND member_id = %(member_id)s',
            team_id=team_id,
            member_id=member_id,
            role=role,
    ):
        pass


async def delete_member(team_id: int, member_id: int):
    async with SafeExecutor(
            event='HARD DELETE team member',
            sql=r'DELETE FROM team_member'
                r'      WHERE team_id = %(team_id)s AND member_id = %(member_id)s',
            team_id=team_id,
            member_id=member_id,
    ):
        pass
