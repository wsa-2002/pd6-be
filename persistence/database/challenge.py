from datetime import datetime
from typing import Optional, Sequence

from base import do, enum
from base.popo import Filter, Sorter
from util.context import context

from . import peer_review, problem
from .base import AutoTxConnection, OnlyExecute, FetchOne, FetchAll, ParamDict
from .util import execute_count, compile_filters


async def add(class_id: int, publicize_type: enum.ChallengePublicizeType, selection_type: enum.TaskSelectionType,
              title: str, setter_id: int, description: Optional[str],
              start_time: datetime, end_time: datetime) -> int:
    async with FetchOne(
            event='Add challenge',
            sql="INSERT INTO challenge"
                "            (class_id, publicize_type, selection_type,"
                "             title, setter_id, description, start_time, end_time)"
                "     VALUES (%(class_id)s, %(publicize_type)s, %(selection_type)s, %(title)s, %(setter_id)s,"
                "             %(description)s, %(start_time)s, %(end_time)s)"
                "  RETURNING id",
            class_id=class_id, publicize_type=publicize_type, selection_type=selection_type,
            title=title, setter_id=setter_id, description=description, start_time=start_time, end_time=end_time,
    ) as (id_,):
        return id_


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter],
                 exclude_scheduled: bool = False, ref_time: datetime = None,
                 include_deleted: bool = False, by_publicize_type: bool = False) -> tuple[Sequence[do.Challenge], int]:
    if not ref_time:
        ref_time = context.request_time

    if exclude_scheduled:
        filters += [Filter(col_name='start_time',
                           op=enum.FilterOperator.le,
                           value=ref_time)]
    if not include_deleted:
        filters += [Filter(col_name='is_deleted',
                           op=enum.FilterOperator.eq,
                           value=include_deleted)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    # FIXME: This looks really ugly, only for temp 'All Class'
    async with FetchAll(
            event='browse challenges',
            sql=fr'SELECT id, class_id, publicize_type, selection_type, title, setter_id, description,'
                fr'       start_time, end_time, is_deleted'
                fr'  FROM challenge'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr'{"  WHERE" if (not cond_sql) and by_publicize_type else ""}'
                fr'{"    AND" if cond_sql and by_publicize_type else ""}'
                fr'{" ((publicize_type = %(end_time)s AND end_time <= %(ref_time)s)" if by_publicize_type else ""}'
                fr'{"   OR (publicize_type = %(start_time)s AND start_time <= %(ref_time)s))" if by_publicize_type else ""}'
                fr' ORDER BY {sort_sql} class_id ASC, id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            end_time=enum.ChallengePublicizeType.end_time, start_time=enum.ChallengePublicizeType.start_time,
            limit=limit, offset=offset, ref_time=ref_time,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.Challenge(id=id_, class_id=class_id, publicize_type=enum.ChallengePublicizeType(publicize_type),
                             selection_type=enum.TaskSelectionType(selection_type), title=title,
                             setter_id=setter_id, description=description, start_time=start_time, end_time=end_time,
                             is_deleted=is_deleted)
                for (id_, class_id, publicize_type, selection_type, title, setter_id, description,
                     start_time, end_time, is_deleted)
                in records]
    total_count = await execute_count(
        sql=fr'SELECT id, class_id, publicize_type, selection_type, title,'
            fr'       setter_id, description, start_time, end_time, is_deleted'
            fr'  FROM challenge'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
            fr'{"  WHERE" if (not cond_sql) and by_publicize_type else ""}'
            fr'{"    AND" if cond_sql and by_publicize_type else ""}'
            fr'{" ((publicize_type = %(end_time)s AND end_time <= %(ref_time)s)" if by_publicize_type else ""}'
            fr'{"   OR (publicize_type = %(start_time)s AND start_time <= %(ref_time)s))" if by_publicize_type else ""}',
        **cond_params,
        end_time=enum.ChallengePublicizeType.end_time, start_time=enum.ChallengePublicizeType.start_time,
        ref_time=ref_time,
    )

    return data, total_count


async def read(challenge_id: int, exclude_scheduled: bool = False, ref_time: datetime = None,
               include_deleted: bool = False) -> do.Challenge:
    async with FetchOne(
            event='read challenge by id',
            sql=fr'SELECT id, class_id, publicize_type, selection_type, title, setter_id, description,'
                fr'       start_time, end_time, is_deleted'
                fr'  FROM challenge'
                fr' WHERE id = %(challenge_id)s'
                fr'{" AND start_time <= %(ref_time)s" if exclude_scheduled else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            challenge_id=challenge_id,
            ref_time=ref_time or context.request_time,
    ) as (id_, class_id, publicize_type, selection_type, title, setter_id, description,
          start_time, end_time, is_deleted):
        return do.Challenge(id=id_, class_id=class_id, publicize_type=enum.ChallengePublicizeType(publicize_type),
                            selection_type=enum.TaskSelectionType(selection_type), title=title,
                            setter_id=setter_id, description=description, start_time=start_time, end_time=end_time,
                            is_deleted=is_deleted)


async def edit(challenge_id: int,
               publicize_type: enum.ChallengePublicizeType = None,
               selection_type: enum.TaskSelectionType = None,
               title: str = None,
               description: Optional[str] = ...,
               start_time: datetime = None,
               end_time: datetime = None, ) -> None:
    to_updates: ParamDict = {}

    if publicize_type is not None:
        to_updates['publicize_type'] = publicize_type
    if selection_type is not None:
        to_updates['selection_type'] = selection_type
    if title is not None:
        to_updates['title'] = title
    if description is not ...:
        to_updates['description'] = description
    if start_time is not None:
        to_updates['start_time'] = start_time
    if end_time is not None:
        to_updates['end_time'] = end_time

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='edit challenge',
            sql=fr'UPDATE challenge'
                fr'   SET {set_sql}'
                fr' WHERE id = %(challenge_id)s',
            challenge_id=challenge_id,
            **to_updates,
    ):
        pass


async def delete(challenge_id: int) -> None:
    async with OnlyExecute(
            event='soft delete challenge',
            sql=r'UPDATE challenge'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(challenge_id)s',
            challenge_id=challenge_id,
            is_deleted=True,
    ):
        pass


async def delete_cascade(challenge_id: int) -> None:
    async with AutoTxConnection(event=f'cascade delete from challenge {challenge_id=}') as conn:
        await peer_review.delete_cascade_from_challenge(challenge_id=challenge_id, cascading_conn=conn)
        await problem.delete_cascade_from_challenge(challenge_id=challenge_id, cascading_conn=conn)

        await conn.execute(r'UPDATE challenge'
                           r'   SET is_deleted = $1'
                           r' WHERE id = $2',
                           True, challenge_id)


async def delete_cascade_from_class(class_id: int, cascading_conn=None) -> None:
    if cascading_conn:
        await _delete_cascade_from_class(class_id, conn=cascading_conn)
        return

    async with AutoTxConnection(event=f'cascade delete challenge from class {class_id=}') as conn:
        await _delete_cascade_from_class(class_id, conn=conn)


async def _delete_cascade_from_class(class_id: int, conn) -> None:
    await conn.execute(r'UPDATE challenge'
                       r'   SET is_deleted = $1'
                       r' WHERE class_id = $2',
                       True, class_id)
