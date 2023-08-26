from datetime import datetime
from typing import Sequence

from base import do
from base.enum import FilterOperator
from base.popo import Filter, Sorter
from util.context import context

from .base import FetchOne, FetchAll, OnlyExecute, ParamDict
from .util import execute_count, compile_filters


async def add(title: str, content: str, author_id: int, post_time: datetime, expire_time: datetime) \
        -> int:
    async with FetchOne(
            event='Add announcement',
            sql=r'INSERT INTO announcement'
                r'            (title, content, author_id, post_time, expire_time)'
                r'     VALUES (%(title)s, %(content)s, %(author_id)s, %(post_time)s, %(expire_time)s)'
                r'  RETURNING id',
            title=title, content=content, author_id=author_id, post_time=post_time, expire_time=expire_time,
    ) as (announcement_id,):
        return announcement_id


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter],
                 include_deleted=False, exclude_scheduled=False, ref_time: datetime = None) \
        -> tuple[Sequence[do.Announcement], int]:
    if exclude_scheduled:
        filters += [Filter(col_name='post_time',
                           op=FilterOperator.le,
                           value=ref_time or context.request_time)]
    if not include_deleted:
        filters += [Filter(col_name='is_deleted',
                           op=FilterOperator.eq,
                           value=include_deleted)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='get all announcements',
            sql=fr'SELECT id, title, content, author_id, post_time, expire_time, is_deleted'
                fr'  FROM announcement'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.Announcement(id=id_, title=title, content=content, author_id=author_id,
                                post_time=post_time, expire_time=expire_time, is_deleted=is_deleted)
                for (id_, title, content, author_id, post_time, expire_time, is_deleted) in records]

    total_count = await execute_count(
        sql=fr'SELECT id, title, content, author_id, post_time, expire_time, is_deleted'
            fr'  FROM announcement'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def read(announcement_id: int, include_deleted=False, exclude_scheduled=False, ref_time: datetime = None) \
        -> do.Announcement:
    if exclude_scheduled and not ref_time:
        ref_time = context.request_time

    async with FetchOne(
            event='get all announcements',
            sql=fr'SELECT id, title, content, author_id, post_time, expire_time, is_deleted'
                fr'  FROM announcement'
                fr' WHERE id = %(announcement_id)s'
                fr'{" AND post_time <= %(ref_time)s" if exclude_scheduled else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            announcement_id=announcement_id,
            ref_time=ref_time,
    ) as (id_, title, content, author_id, post_time, expire_time, is_deleted):
        return do.Announcement(id=id_, title=title, content=content, author_id=author_id,
                               post_time=post_time, expire_time=expire_time, is_deleted=is_deleted)


async def edit(announcement_id: int, title: str = None, content: str = None,
               post_time: datetime = None, expire_time: datetime = None) -> None:
    to_updates: ParamDict = {}

    if title is not None:
        to_updates['title'] = title
    if content is not None:
        to_updates['content'] = content
    if post_time is not None:
        to_updates['post_time'] = post_time
    if expire_time is not None:
        to_updates['expire_time'] = expire_time

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='update announcement by id',
            sql=fr'UPDATE announcement'
                fr'   SET {set_sql}'
                fr' WHERE id = %(announcement_id)s',
            announcement_id=announcement_id,
            **to_updates,
    ):
        pass


async def delete(announcement_id: int) -> None:
    async with OnlyExecute(
            event='soft delete announcement',
            sql=r'UPDATE announcement'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(announcement_id)s',
            announcement_id=announcement_id,
            is_deleted=True,
    ):
        pass
