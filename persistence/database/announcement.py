from datetime import datetime
from typing import Sequence

import log
from base import do

from .base import SafeExecutor


async def add(title: str, content: str, author_id: int, post_time: datetime, expire_time: datetime) \
        -> int:
    async with SafeExecutor(
            event='Add announcement',
            sql=r'INSERT INTO announcement'
                r'            (title, content, author_id, post_time, expire_time)'
                r'     VALUES (%(title)s, %(content)s, %(author_id)s, %(post_time)s, %(expire_time)s)'
                r'  RETURNING id',
            title=title, content=content, author_id=author_id, post_time=post_time, expire_time=expire_time,
            fetch=1,
    ) as (announcement_id,):
        return announcement_id


async def browse(include_scheduled: bool, ref_time: datetime = None, include_deleted=False) \
        -> Sequence[do.Announcement]:
    """
    ref_time must be given if include_scheduled is False
    """
    filters = []
    if not include_scheduled:
        if not ref_time:
            raise ValueError
        filters.append("post_time <= %(ref_time)s AND expire_time > %(ref_time)s")
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(filters)

    async with SafeExecutor(
            event='get all announcements',
            sql=fr'SELECT id, title, content, author_id, post_time, expire_time, is_deleted'
                fr'  FROM announcement'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            ref_time=ref_time,
            fetch='all',
    ) as records:
        return [do.Announcement(id=id_, title=title, content=content, author_id=author_id,
                                post_time=post_time, expire_time=expire_time, is_deleted=is_deleted)
                for (id_, title, content, author_id, post_time, expire_time, is_deleted) in records]


async def read(announcement_id: int, include_scheduled: bool, ref_time: datetime = None, include_deleted=False) \
        -> do.Announcement:
    """
    ref_time must be given if include_scheduled is False
    """
    if not include_scheduled and not ref_time:
        raise ValueError
    async with SafeExecutor(
            event='get all announcements',
            sql=fr'SELECT id, title, content, author_id, post_time, expire_time, is_deleted'
                fr'  FROM announcement'
                fr' WHERE id = %(announcement_id)s'
                fr'{" AND post_time <= %(ref_time)s AND expire_time > %(ref_time)s" if not include_scheduled else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            announcement_id=announcement_id,
            ref_time=ref_time,
            fetch=1,
    ) as (id_, title, content, author_id, post_time, expire_time, is_deleted):
        return do.Announcement(id=id_, title=title, content=content, author_id=author_id,
                               post_time=post_time, expire_time=expire_time, is_deleted=is_deleted)


async def edit(announcement_id: int, title: str = None, content: str = None,
               post_time: datetime = None, expire_time: datetime = None) -> None:
    to_updates = {}

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

    async with SafeExecutor(
            event='update announcement by id',
            sql=fr'UPDATE announcement'
                fr'   SET {set_sql}'
                fr' WHERE id = %(announcement_id)s',
            announcement_id=announcement_id,
            **to_updates,
    ):
        pass


async def delete(announcement_id: int) -> None:
    async with SafeExecutor(
            event='soft delete announcement',
            sql=fr'UPDATE announcement'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(announcement_id)s',
            announcement_id=announcement_id,
            is_deleted=True,
    ):
        pass
