from itertools import chain
from operator import itemgetter
from typing import Sequence, Tuple

import asyncpg

import exceptions as exc
import log
from base import do
from base.enum import RoleType, FilterOperator
from base.popo import Filter, Sorter

from .base import AutoTxConnection, FetchOne, FetchAll, OnlyExecute, ParamDict
from .util import execute_count, compile_filters, compile_values
from .account import account_referral_to_id


async def add(name: str, class_id: int, label: str) -> int:
    async with FetchOne(
            event='add team',
            sql=r'INSERT INTO team'
                r'            (name, class_id, label)'
                r'     VALUES (%(name)s, %(class_id)s, %(label)s)'
                r'  RETURNING id',
            name=name,
            class_id=class_id,
            label=label,
    ) as (team_id,):
        return team_id


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter],
                 include_deleted=False) -> tuple[Sequence[do.Team], int]:
    if not include_deleted:
        filters += [Filter(col_name='is_deleted',
                           op=FilterOperator.eq,
                           value=include_deleted)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse teams',
            sql=fr'SELECT id, name, class_id, is_deleted, label'
                fr'  FROM team'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} class_id ASC, id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.Team(id=id_, name=name, class_id=class_id, is_deleted=is_deleted, label=label)
                for (id_, name, class_id, is_deleted, label) in records]

    total_count = await execute_count(
        sql=fr'SELECT id, name, class_id, is_deleted, label'
            fr'  FROM team'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def browse_with_team_label_filter(class_id: int, team_label_filter: str = None) -> Sequence[do.Team]:
    """
    :raises exc.InvalidTeamLabelFilter
    """
    async with FetchAll(
            event='browse teams with team label filter',
            sql=fr'SELECT team.id, team.name, team.class_id, team.is_deleted, team.label'
                fr'  FROM team'
                fr' INNER JOIN class'
                fr'         ON class.id = team.class_id'
                fr'{"   WHERE team.label ~ %(team_label_filter)s" if team_label_filter else ""}'
                fr'   AND class.id = %(class_id)s'
                fr'   AND NOT team.is_deleted',
            team_label_filter=team_label_filter,
            class_id=class_id,
            raise_not_found=False,  # Issue #134: return [] for browse
            exception_mapping={
                asyncpg.InvalidRegularExpressionError: exc.InvalidTeamLabelFilter,
            },
    ) as records:
        return [do.Team(id=id_, name=name, class_id=class_id, is_deleted=is_deleted, label=label)
                for (id_, name, class_id, is_deleted, label) in records]


async def read(team_id: int, *, include_deleted=False) -> do.Team:
    async with FetchOne(
            event='get team by id',
            sql=fr'SELECT id, name, class_id, is_deleted, label'
                fr'  FROM team'
                fr' WHERE id = %(team_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            team_id=team_id,
    ) as (id_, name, class_id, is_deleted, label):
        return do.Team(id=id_, name=name, class_id=class_id, is_deleted=is_deleted, label=label)


async def edit(team_id: int, name: str = None, class_id: int = None, label: str = None):
    to_updates: ParamDict = {}

    if name is not None:
        to_updates['name'] = name
    if class_id is not None:
        to_updates['class_id'] = class_id
    if label is not None:
        to_updates['label'] = label

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='update team by id',
            sql=fr'UPDATE team'
                fr'   SET {set_sql}'
                fr' WHERE id = %(team_id)s',
            team_id=team_id,
            **to_updates,
    ):
        pass


async def delete(team_id: int) -> None:
    async with OnlyExecute(
            event='soft delete team',
            sql=r'UPDATE team'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(team_id)s',
            team_id=team_id,
            is_deleted=True,
    ):
        pass


async def delete_cascade_from_class(class_id: int, cascading_conn=None) -> None:
    if cascading_conn:
        await _delete_cascade_from_class(class_id, conn=cascading_conn)
        return

    async with AutoTxConnection(event=f'cascade delete team from class {class_id=}') as conn:
        await _delete_cascade_from_class(class_id, conn=conn)


async def _delete_cascade_from_class(class_id: int, conn) -> None:
    await conn.execute(r'UPDATE team'
                       r'   SET is_deleted = $1'
                       r' WHERE class_id = $2',
                       True, class_id)


# === member control


async def browse_members(team_id: int) -> Sequence[do.TeamMember]:
    async with FetchAll(
            event='get team members id',
            sql=r'SELECT member_id, team_id, role'
                r'  FROM team_member'
                r' WHERE team_id = %(team_id)s'
                r' ORDER BY role DESC',
            team_id=team_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.TeamMember(member_id=id_, team_id=team_id, role=RoleType(role_str))
                for id_, team_id, role_str in records]


async def read_member(team_id: int, member_id: int) -> do.TeamMember:
    async with FetchOne(
            event='get team member role',
            sql=r'SELECT member_id, team_id, role'
                r'  FROM team_member'
                r' WHERE team_id = %(team_id)s and member_id = %(member_id)s',
            team_id=team_id,
            member_id=member_id,
    ) as (member_id, team_id, role):
        return do.TeamMember(member_id=member_id, team_id=team_id, role=RoleType(role))


async def add_member(team_id: int, account_referral: str, role: RoleType):
    async with OnlyExecute(
            event='add team member',
            sql=r'INSERT INTO team_member'
                r'            (team_id, member_id, role)'
                r'     VALUES (%(team_id)s, account_referral_to_id(%(account_referral)s), %(role)s)',
            team_id=team_id, account_referral=account_referral, role=role,
    ):
        pass


async def add_members(team_id: int, member_roles: Sequence[Tuple[str, RoleType]]) -> Sequence[bool]:
    """
    :return: a list of bool indicating if the insertion is successful (true) or not (false)
    """
    if not member_roles:
        return []

    async with AutoTxConnection(event=f'add members to team {team_id=}') as conn:
        # 1. get the referrals
        value_sql, value_params = compile_values([
            (account_referral,)
            for account_referral, _ in member_roles
        ])
        log.info(f'Fetching account ids with values {value_params}')
        account_ids: list[list[int]] = await conn.fetch(
            fr'  WITH account_referrals (account_referral)'
            fr'    AS (VALUES {value_sql})'
            fr'SELECT account_referral_to_id(account_referral)'
            fr'  FROM account_referrals',
            *value_params,
        )
        log.info(f'Fetched account ids: {account_ids}')

        # 2. perform insert
        value_sql, value_params = compile_values(sorted((
            (team_id, account_id, role)
            for (account_id,), (_, role) in zip(account_ids, member_roles)
            if account_id is not None
        ), key=itemgetter(2), reverse=True))
        log.info(f'Inserting new team members with values {value_params}')

        if not value_sql:
            raise exc.IllegalInput

        inserted_account_ids: list[list[int]] = await conn.fetch(
            fr' INSERT INTO team_member'
            fr'            (team_id, member_id, role)'
            fr'     VALUES {value_sql}'
            fr' ON CONFLICT DO NOTHING'
            fr'   RETURNING member_id',
            *value_params,
        )
        log.info(f'Inserted {len(inserted_account_ids)} out of {len(account_ids)} given new team members')

    # 3. check the failed account ids
    success_account_ids = set(chain(*inserted_account_ids))
    return [account_id in success_account_ids for account_id in chain(*account_ids)]


async def add_team_and_add_member(class_id: int, team_label: str,
                                  datas: Sequence[tuple[str, Sequence[tuple[str, RoleType]]]]):
    async with AutoTxConnection(event='add member with team name') as conn:
        try:
            for team_name, member_roles in datas:
                (team_id,) = await conn.fetchrow(
                    r'WITH get AS ('
                    r'     SELECT id'
                    r'       FROM team'
                    r'      WHERE team.name = $1'
                    r'        AND team.class_id = $2'
                    r'        AND team.label = $3'
                    r'        AND is_deleted = $4'
                    r'), new_team AS ('
                    r'     INSERT INTO team'
                    r'                 (name, class_id, label)'
                    r'          VALUES ($1, $2, $3)'
                    r'     ON CONFLICT DO NOTHING'
                    r'     RETURNING id'
                    r')'
                    r'SELECT id FROM get'
                    r' UNION ALL'
                    r' SELECT id FROM new_team',
                    team_name, class_id, team_label, False,
                )

                values = [(team_id,
                           await account_referral_to_id(account_referral),
                           role)
                          for account_referral, role in member_roles]

                value_sql, value_params = compile_values(values=values)

                await conn.execute(
                    fr'INSERT INTO team_member'
                    fr'            (team_id, member_id, role)'
                    fr'     VALUES {value_sql}',
                    *value_params
                )
        except asyncpg.exceptions.UniqueViolationError:
            raise exc.persistence.UniqueViolationError


async def edit_member(team_id: int, member_id: int, role: RoleType):
    async with OnlyExecute(
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
    async with OnlyExecute(
            event='HARD DELETE team member',
            sql=r'DELETE FROM team_member'
                r'      WHERE team_id = %(team_id)s AND member_id = %(member_id)s',
            team_id=team_id,
            member_id=member_id,
    ):
        pass
