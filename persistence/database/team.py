from typing import Tuple, Collection, Sequence

from base import do
from base.enum import RoleType

from .base import SafeExecutor


async def add(name: str, class_id: int, is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='create team',
            sql=r'INSERT INTO team'
                r'            (name, class_id, is_enabled, is_hidden)'
                r'     VALUES (%(name)s, %(class_id)s), %(is_enabled)s), %(is_hidden)s)'
                r'  RETURNING id',
            name=name,
            class_id=class_id,
            is_enabled=is_enabled,
            is_hidden=is_hidden,
            fetch=1,
    ) as (class_id,):
        return class_id
        

async def browse(class_id: int = None, only_enabled=True, exclude_hidden=True) -> Sequence[do.Team]:
    conditions = {}

    if class_id is not None:
        conditions['class_id'] = class_id
    if only_enabled:
        conditions['is_enabled'] = True
    if exclude_hidden:
        conditions['is_hidden'] = False

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='get all teams',
            sql=fr'SELECT id, name, class_id, is_enabled, is_hidden'
                fr'  FROM course'
                fr' {f"WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY class_id ASC, id ASC',
            fetch='all',
    ) as records:
        return [do.Team(id=id_, name=name, class_id=c_id,
                        is_enabled=is_enabled, is_hidden=is_hidden)
                for (id_, name, c_id, is_enabled, is_hidden) in records]


async def read(team_id: int, only_enabled=True, exclude_hidden=True) -> do.Team:
    conditions = []
    if only_enabled:
        conditions.append('is_enabled = TRUE')
    if exclude_hidden:
        conditions.append('is_hidden = FALSE')
    cond_sql = ' AND '.join(conditions)

    async with SafeExecutor(
            event='get team by id',
            sql=fr'SELECT id, name, class_id, is_enabled, is_hidden'
                fr'  FROM team'
                fr' WHERE id = %(team_id)s'
                fr'{" AND " + cond_sql if cond_sql else ""}',
            team_id=team_id,
            fetch=1,
    ) as (id_, name, c_id, is_enabled, is_hidden):
        return do.Team(id=id_, name=name, class_id=c_id,
                       is_enabled=is_enabled, is_hidden=is_hidden)


async def edit(team_id: int, name: str = None, class_id: int = None,
               is_enabled: bool = None, is_hidden: bool = None):
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if class_id is not None:
        to_updates['class_id'] = class_id
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_enabled

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update team by id',
            sql=fr'UPDATE team'
                fr' WHERE team.id = %(team_id)s'
                fr'   SET {set_sql}',
            team_id=team_id,
            **to_updates,
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
                r' WHERE team_id = %(team_id)s AND member_id = %(member_id)s'
                r'   SET role = %(role)s',
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
