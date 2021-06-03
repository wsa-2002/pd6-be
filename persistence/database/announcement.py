from datetime import datetime
from typing import Sequence

from base import do

from .base import SafeExecutor


async def add(title: str, content: str, author_id: int, post_time: datetime, expire_time: datetime) -> int:
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


async def browse(show_hidden: bool) -> Sequence[do.Announcement]:
    async with SafeExecutor(
            event='get all announcements',
            sql=fr'SELECT id, title, content, author_id, post_time, expire_time'
                fr'  FROM announcement'
                fr' {"WHERE post_time <= %(cur_time)s AND expire_time > %(cur_time)s" if not show_hidden else ""}'
                fr' ORDER BY id ASC',
            cur_time=datetime.now(),
            fetch='all',
    ) as records:
        return [do.Announcement(id=id_, title=title, content=content, author_id=author_id,
                                post_time=post_time, expire_time=expire_time)
                for (id_, title, content, author_id, post_time, expire_time) in records]


async def read(announcement_id: int, show_hidden: bool) -> do.Announcement:
    async with SafeExecutor(
            event='get all announcements',
            sql=fr'SELECT id, title, content, author_id, post_time, expire_time'
                fr'  FROM announcement'
                fr' WHERE id = %(announcement_id)s'
                fr' {"AND post_time <= %(cur_time)s AND expire_time > %(cur_time)s" if not show_hidden else ""}',
            announcement_id=announcement_id,
            cur_time=datetime.now(),
            fetch=1,
    ) as (id_, title, content, author_id, post_time, expire_time):
        return do.Announcement(id=id_, title=title, content=content, author_id=author_id,
                               post_time=post_time, expire_time=expire_time)


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
                fr' WHERE announcement.id = %(announcement_id)s'
                fr'   SET {set_sql}',
            announcement_id=announcement_id,
            **to_updates,
    ):
        pass


async def delete(announcement_id: int) -> None:
    async with SafeExecutor(
            event='delete announcement by id',
            sql=fr'DELETE FROM announcement'
                fr'      WHERE announcement.id = %(announcement_id)s',
            announcement_id=announcement_id,
    ):
        pass