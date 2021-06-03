from datetime import datetime
from typing import Optional, Sequence

from base import do, enum

from .base import SafeExecutor


async def add(target_challenge_id: int, target_problem_id: int, setter_id: int, description: str,
              min_score: int, max_score: int, max_review_count: int, start_time: datetime, end_time: datetime,
              is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='Add peer review',
            sql="INSERT INTO peer_review"
                "            (target_challenge_id, target_problem_id, setter_id, description,"
                "             min_score, max_score, max_review_count, start_time, end_time,"
                "             is_enabled, is_hidden)"
                "     VALUES (%(target_challenge_id)s, %(target_problem_id)s, %(setter_id)s, %(description)s,"
                "             %(min_score)s, %(max_score)s, %(max_review_count)s, %(start_time)s, %(end_time)s,"
                "             %(is_enabled)s, %(is_hidden)s)"
                "  RETURNING id",
            target_challenge_id=target_challenge_id, target_problem_id=target_problem_id,
            setter_id=setter_id, description=description,
            min_score=min_score, max_score=max_score, max_review_count=max_review_count,
            start_time=start_time, end_time=end_time, is_enabled=is_enabled, is_hidden=is_hidden,
            fetch=1,
    ) as (id_,):
        return id_


async def browse() -> Sequence[do.PeerReview]:
    async with SafeExecutor(
            event='browse peer reviews',
            sql=fr'SELECT id, target_challenge_id, target_problem_id, setter_id, description,'
                '         min_score, max_score, max_review_count, start_time, end_time,'
                '         is_enabled, is_hidden'
                fr'  FROM peer_review'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.PeerReview(id=id_, target_challenge_id=target_challenge_id, target_problem_id=target_problem_id,
                              setter_id=setter_id, description=description,
                              min_score=min_score, max_score=max_score, max_review_count=max_review_count,
                              start_time=start_time, end_time=end_time, is_enabled=is_enabled, is_hidden=is_hidden)
                for (id_, target_challenge_id, target_problem_id, setter_id, description, min_score, max_score,
                     max_review_count, start_time, end_time, is_enabled, is_hidden)
                in records]


async def read(peer_review_id: int) -> do.PeerReview:
    async with SafeExecutor(
            event='browse peer reviews',
            sql=fr'SELECT id, target_challenge_id, target_problem_id, setter_id, description,'
                '         min_score, max_score, max_review_count, start_time, end_time,'
                '         is_enabled, is_hidden'
                fr'  FROM peer_review'
                fr' WHERE id = %(peer_review_id)s',
            peer_review_id=peer_review_id,
            fetch='all',
    ) as (id_, target_challenge_id, target_problem_id, setter_id, description, min_score, max_score, max_review_count,
          start_time, end_time, is_enabled, is_hidden):
        return do.PeerReview(id=id_, target_challenge_id=target_challenge_id, target_problem_id=target_problem_id,
                             setter_id=setter_id, description=description,
                             min_score=min_score, max_score=max_score, max_review_count=max_review_count,
                             start_time=start_time, end_time=end_time, is_enabled=is_enabled, is_hidden=is_hidden)


async def edit(peer_review_id: int, description: str = None, min_score: int = None, max_score: int = None,
               max_review_count: int = None, start_time: datetime = None, end_time: datetime = None,
               is_enabled: bool = None, is_hidden: bool = None) -> None:
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
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit peer review',
            sql=fr'UPDATE peer_review'
                fr' WHERE id = %(peer_review_id)s'
                fr'   SET {set_sql}',
            peer_review_id=peer_review_id,
            **to_updates,
    ):
        pass


async def delete(peer_review_id: int) -> None:
    ...  # TODO
