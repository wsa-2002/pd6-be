from datetime import datetime
from typing import Optional, Sequence

from base import do, enum

from .base import SafeExecutor


async def add(peer_review_id: int, grader_id: int, receiver_id: int, submission_id: int) -> int:
    """
    Assign a new peer review record
    """
    async with SafeExecutor(
            event='Add (assign) peer review record',
            sql="INSERT INTO peer_review_record"
                "            (peer_review_id, grader_id, receiver_id, submission_id)"
                "     VALUES (%(peer_review_id)s, %(grader_id)s, %(receiver_id)s, %(submission_id)s)"
                "  RETURNING id",
            peer_review_id=peer_review_id, grader_id=grader_id, receiver_id=receiver_id, submission_id=submission_id,
            fetch=1,
    ) as (id_,):
        return id_


async def edit_score(peer_review_record_id: int, score: int, comment: str, submit_time: datetime = None) -> None:
    """Allows only full edit!"""
    if submit_time is None:
        submit_time = datetime.now()

    async with SafeExecutor(
            event='Add (submit) peer review record (score)',
            sql="UPDATE peer_review_record"
                " WHERE id = %(peer_review_record_id)s"
                "   SET score = %(score)s, comment = %(comment)s, submit_time = %(submit_time)s",
            peer_review_record_id=peer_review_record_id,
            score=score, comment=comment, submit_time=submit_time,
    ):
        pass


async def browse(grader_id: int = None, receiver_id: int = None) -> Sequence[do.PeerReviewRecord]:
    conditions = {}

    if grader_id is not None:
        conditions['grader_id'] = grader_id
    if receiver_id is not None:
        conditions['receiver_id'] = receiver_id

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='browse peer review records',
            sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, submission_id, score, comment, submit_time'
                fr'  FROM peer_review_record'
                fr' {f"WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.PeerReviewRecord(id=id_, peer_review_id=peer_review_id,
                                    grader_id=grader_id, receiver_id=receiver_id, submission_id=submission_id,
                                    score=score, comment=comment, submit_time=submit_time)
                for (id_, peer_review_id, grader_id, receiver_id, submission_id, score, comment, submit_time)
                in records]


async def read(peer_review_record_id: int) -> do.PeerReviewRecord:
    async with SafeExecutor(
            event='read peer review record',
            sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, submission_id, score, comment, submit_time'
                fr'  FROM peer_review_record'
                fr' WHERE id = %(peer_review_record_id)s',
            peer_review_record_id=peer_review_record_id,
            fetch=1,
    ) as (id_, peer_review_id, grader_id, receiver_id, submission_id, score, comment, submit_time):
        return do.PeerReviewRecord(id=id_, peer_review_id=peer_review_id,
                                   grader_id=grader_id, receiver_id=receiver_id, submission_id=submission_id,
                                   score=score, comment=comment, submit_time=submit_time)
