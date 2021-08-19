from datetime import datetime
from typing import Sequence

from base import do
from base.popo import Filter, Sorter

from .base import SafeExecutor
from .util import execute_count, compile_filters


async def add(peer_review_id: int, grader_id: int, receiver_id: int) -> int:
    """
    Assign a new peer review record
    """
    async with SafeExecutor(
            event='Add (assign) peer review record',
            sql="INSERT INTO peer_review_record"
                "            (peer_review_id, grader_id, receiver_id)"
                "     VALUES (%(peer_review_id)s, %(grader_id)s, %(receiver_id)s)"
                "  RETURNING id",
            peer_review_id=peer_review_id, grader_id=grader_id, receiver_id=receiver_id,
            fetch=1,
    ) as (id_,):
        return id_


async def edit_score(peer_review_record_id: int, score: int, comment: str, submit_time: datetime) -> None:
    """Allows only full edit!"""
    async with SafeExecutor(
            event='Add (submit) peer review record (score)',
            sql="UPDATE peer_review_record"
                "   SET score = %(score)s, comment = %(comment)s, submit_time = %(submit_time)s"
                " WHERE id = %(peer_review_record_id)s",
            peer_review_record_id=peer_review_record_id,
            score=score, comment=comment, submit_time=submit_time,
    ):
        pass


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[do.PeerReviewRecord], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with SafeExecutor(
            event='browse peer review records',
            sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time'
                fr'  FROM peer_review_record'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,
    ) as records:
        data = [do.PeerReviewRecord(id=id_, peer_review_id=peer_review_id,
                                    grader_id=grader_id, receiver_id=receiver_id,
                                    score=score, comment=comment, submit_time=submit_time)
                for (id_, peer_review_id, grader_id, receiver_id, score, comment, submit_time)
                in records]
    total_count = await execute_count(
        sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time'
            fr'  FROM peer_review_record'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def read(peer_review_record_id: int) -> do.PeerReviewRecord:
    async with SafeExecutor(
            event='read peer review record',
            sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time'
                fr'  FROM peer_review_record'
                fr' WHERE id = %(peer_review_record_id)s',
            peer_review_record_id=peer_review_record_id,
            fetch=1,
    ) as (id_, peer_review_id, grader_id, receiver_id, score, comment, submit_time):
        return do.PeerReviewRecord(id=id_, peer_review_id=peer_review_id,
                                   grader_id=grader_id, receiver_id=receiver_id,
                                   score=score, comment=comment, submit_time=submit_time)
