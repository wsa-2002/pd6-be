from datetime import datetime
from typing import Sequence

from base import do

from .base import SafeExecutor


async def add(target_task_id: int, setter_id: int, description: str,
              min_score: int, max_score: int, max_review_count: int, start_time: datetime, end_time: datetime,
              is_hidden: bool, is_deleted: bool) -> int:
    async with SafeExecutor(
            event='Add peer review',
            sql="INSERT INTO peer_review"
                "            (target_task_id, setter_id, description,"
                "             min_score, max_score, max_review_count, start_time, end_time,"
                "             is_hidden, is_deleted)"
                "     VALUES (%(target_task_id)s, %(setter_id)s, %(description)s,"
                "             %(min_score)s, %(max_score)s, %(max_review_count)s, %(start_time)s, %(end_time)s,"
                "             %(is_enabled)s, %(is_hidden)s)"
                "  RETURNING id",
            target_task_id=target_task_id,
            setter_id=setter_id, description=description,
            min_score=min_score, max_score=max_score, max_review_count=max_review_count,
            start_time=start_time, end_time=end_time, is_hidden=is_hidden, is_deleted=is_deleted,
            fetch=1,
    ) as (id_,):
        return id_


async def browse(include_deleted=False) -> Sequence[do.PeerReview]:
    async with SafeExecutor(
            event='browse peer reviews',
            sql=fr'SELECT id, target_task_id, setter_id, description,'
                fr'       min_score, max_score, max_review_count, start_time, end_time,'
                fr'       is_hidden, is_deleted'
                fr'  FROM peer_review'
                fr'{" WHERE NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.PeerReview(id=id_, target_task_id=target_task_id,
                              setter_id=setter_id, description=description,
                              min_score=min_score, max_score=max_score, max_review_count=max_review_count,
                              start_time=start_time, end_time=end_time, is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, target_task_id, setter_id, description, min_score, max_score,
                     max_review_count, start_time, end_time, is_hidden, is_deleted)
                in records]


async def read(peer_review_id: int, include_deleted=False) -> do.PeerReview:
    async with SafeExecutor(
            event='browse peer reviews',
            sql=fr'SELECT id, target_task_id, setter_id, description,'
                fr'       min_score, max_score, max_review_count, start_time, end_time,'
                fr'       is_hidden, is_deleted'
                fr'  FROM peer_review'
                fr' WHERE id = %(peer_review_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            peer_review_id=peer_review_id,
            fetch='all',
    ) as (id_, target_task_id, setter_id, description, min_score, max_score, max_review_count,
          start_time, end_time, is_hidden, is_deleted):
        return do.PeerReview(id=id_, target_task_id=target_task_id,
                             setter_id=setter_id, description=description,
                             min_score=min_score, max_score=max_score, max_review_count=max_review_count,
                             start_time=start_time, end_time=end_time, is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(peer_review_id: int, description: str = None, min_score: int = None, max_score: int = None,
               max_review_count: int = None, start_time: datetime = None, end_time: datetime = None,
               is_hidden: bool = None, is_deleted: bool = None) -> None:
    to_updates = {}

    if description is not None:
        to_updates['description'] = description
    if min_score is not None:
        to_updates['min_score'] = min_score
    if max_score is not None:
        to_updates['max_score'] = max_score
    if max_review_count is not None:
        to_updates['max_review_count'] = max_review_count
    if start_time is not None:
        to_updates['start_time'] = start_time
    if end_time is not None:
        to_updates['end_time'] = end_time
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden
    if is_deleted is not None:
        to_updates['is_deleted'] = is_deleted

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit peer review',
            sql=fr'UPDATE peer_review'
                fr'   SET {set_sql}'
                fr' WHERE id = %(peer_review_id)s',
            peer_review_id=peer_review_id,
            **to_updates,
    ):
        pass


async def delete(peer_review_id: int) -> None:
    async with SafeExecutor(
            event='soft delete peer_review',
            sql=fr'UPDATE peer_review'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(peer_review_id)s',
            peer_review_id=peer_review_id,
            is_deleted=True,
    ):
        pass
