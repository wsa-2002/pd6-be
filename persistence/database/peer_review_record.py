from datetime import datetime
from typing import Sequence

from base import do, enum
from base.popo import Filter, Sorter

from .base import AutoTxConnection, FetchAll, FetchOne, OnlyExecute
from .util import execute_count, compile_filters


async def edit_score(peer_review_record_id: int, score: int, comment: str, submit_time: datetime) -> None:
    """Allows only full edit!"""
    async with OnlyExecute(
            event='Add (submit) peer review record (score)',
            sql="UPDATE peer_review_record"
                "   SET score = %(score)s, comment = %(comment)s, submit_time = %(submit_time)s"
                " WHERE id = %(peer_review_record_id)s",
            peer_review_record_id=peer_review_record_id,
            score=score, comment=comment, submit_time=submit_time,
    ):
        pass


async def browse(peer_review_id: int, limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[do.PeerReviewRecord], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse peer review records',
            sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time, submission_id'
                fr'  FROM peer_review_record'
                fr' WHERE peer_review_id = %(peer_review_id)s'
                fr'{f" AND {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params, peer_review_id=peer_review_id,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.PeerReviewRecord(id=id_, peer_review_id=peer_review_id,
                                    grader_id=grader_id, receiver_id=receiver_id,
                                    score=score, comment=comment, submit_time=submit_time, submission_id=submission_id)
                for (id_, peer_review_id, grader_id, receiver_id, score, comment, submit_time, submission_id)
                in records]
    total_count = await execute_count(
        sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time'
            fr'  FROM peer_review_record'
            fr' WHERE peer_review_id = %(peer_review_id)s'
            fr'{f" AND {cond_sql}" if cond_sql else ""}',
        **cond_params, peer_review_id=peer_review_id,
    )

    return data, total_count


async def read(peer_review_record_id: int) -> do.PeerReviewRecord:
    async with FetchOne(
            event='read peer review record',
            sql=r'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time, submission_id'
                r'  FROM peer_review_record'
                r' WHERE id = %(peer_review_record_id)s',
            peer_review_record_id=peer_review_record_id,
    ) as (id_, peer_review_id, grader_id, receiver_id, score, comment, submit_time, submission_id):
        return do.PeerReviewRecord(id=id_, peer_review_id=peer_review_id,
                                   grader_id=grader_id, receiver_id=receiver_id,
                                   score=score, comment=comment, submit_time=submit_time, submission_id=submission_id)


async def read_by_peer_review_id(peer_review_id: int, account_id: int, is_receiver=True) \
        -> Sequence[do.PeerReviewRecord]:
    async with FetchAll(
            event='read peer review record by peer review id',
            sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time, submission_id'
                fr'  FROM peer_review_record'
                fr' WHERE peer_review_id = %(peer_review_id)s'
                fr'   AND {"receiver_id" if is_receiver else "grader_id"} = %(account_id)s'
                fr' ORDER BY id asc',
            peer_review_id=peer_review_id, account_id=account_id,
            raise_not_found=False,
    ) as records:
        return [do.PeerReviewRecord(id=id_, peer_review_id=peer_review_id,
                                    grader_id=grader_id, receiver_id=receiver_id,
                                    score=score, comment=comment, submit_time=submit_time, submission_id=submission_id)
                for (id_, peer_review_id, grader_id, receiver_id, score, comment, submit_time, submission_id)
                in records]


async def add_auto(peer_review_id: int, grader_id: int) -> int:
    async with AutoTxConnection(event='add auto peer review record') as conn:
        (target_problem_id, challenge_end_time, raw_selection_type, class_id) = await conn.fetchrow(
            r'SELECT peer_review.target_problem_id,'
            r'       challenge.end_time, challenge.selection_type, challenge.class_id'
            r'  FROM peer_review'
            r'  LEFT JOIN problem'
            r'         ON problem.id = peer_review.target_problem_id'
            r'        AND NOT problem.is_deleted'
            r'  LEFT JOIN challenge'
            r'         ON challenge.id = problem.challenge_id'
            r'        AND NOT challenge.is_deleted'
            r' WHERE peer_review.id = $1',
            peer_review_id,
        )
        selection_type = enum.TaskSelectionType(raw_selection_type)

        if selection_type is enum.TaskSelectionType.last:
            (peer_review_record_id,) = await conn.fetchrow(
                r'INSERT INTO peer_review_record'
                r'            (peer_review_id, grader_id, receiver_id, submission_id)'
                r'SELECT $1, $2, member_submission.member_id, member_submission.submission_id'
                r'  FROM ('
                r'       SELECT DISTINCT ON (cm.member_id)'
                r'           cm.member_id AS member_id, submission.id AS submission_id'
                r'         FROM class_member cm'
                r'        INNER JOIN submission'
                r'                ON cm.member_id = submission.account_id'
                r'               AND submission.problem_id = $3'
                r'               AND submission.submit_time <= $4'
                r'        WHERE cm.class_id = $5'
                r'          AND cm."role" = $6'
                r'     ORDER BY cm.member_id, submission.id DESC'
                r'     ) member_submission'
                r'  LEFT JOIN ('
                r'       SELECT cm.member_id AS member_id , count(*) AS count'
                r'         FROM class_member cm'
                r'        INNER JOIN peer_review_record prr'
                r'                ON prr.receiver_id = cm.member_id'
                r'               AND prr.peer_review_id = $1'
                r'        WHERE cm.class_id = $5'
                r'          AND cm."role" = $6'
                r'     GROUP BY cm.member_id'
                r'     ) prr_count'
                r'    ON prr_count.member_id = member_submission.member_id'
                r' WHERE member_submission.member_id != $2'
                r' ORDER BY coalesce(prr_count.count, 0) ASC'
                r' LIMIT 1'
                r' RETURNING id',
                peer_review_id, grader_id, target_problem_id, challenge_end_time, class_id, enum.RoleType.normal,
            )
            return peer_review_record_id

        elif selection_type is enum.TaskSelectionType.best:
            (peer_review_record_id,) = await conn.fetchrow(
                r'INSERT INTO peer_review_record'
                r'            (peer_review_id, grader_id, receiver_id, submission_id)'
                r'SELECT $1, $2, member_submission.member_id, member_submission.submission_id'
                r'  FROM ('
                r'       SELECT DISTINCT ON (cm.member_id)'
                r'              cm.member_id AS member_id, submission_with_score.submission_id AS submission_id'
                r'         FROM class_member cm'
                r'        INNER JOIN ('
                r'              SELECT DISTINCT ON (submission.id)'
                r'                     submission.id AS submission_id, submission.account_id AS account_id,'
                r'                     judgment.score AS score'
                r'                FROM submission'
                r'                LEFT JOIN judgment'
                r'                       ON judgment.submission_id = submission.id'
                r'               WHERE submission.problem_id = $3'
                r'                 AND submission.submit_time <= $4'
                r'            ORDER BY submission.id, judgment.judge_time DESC'
                r'             ) submission_with_score'
                r'            ON cm.member_id = submission_with_score.account_id'
                r'         WHERE cm.class_id = $5'
                r'           AND cm."role" = $6'
                r'      ORDER BY cm.member_id, submission_with_score.score DESC'
                r'     ) member_submission'
                r'  LEFT JOIN ('
                r'       SELECT cm.member_id AS member_id , count(*) AS count'
                r'         FROM class_member cm'
                r'        INNER JOIN peer_review_record prr'
                r'                ON prr.receiver_id = cm.member_id'
                r'               AND prr.peer_review_id = $1'
                r'        WHERE cm.class_id = $5'
                r'          AND cm."role" = $6'
                r'     GROUP BY cm.member_id'
                r'     ) prr_count'
                r'    ON prr_count.member_id = member_submission.member_id'
                r' WHERE member_submission.member_id != $2'
                r' ORDER BY coalesce(prr_count.count, 0) ASC'
                r' LIMIT 1'
                r' RETURNING id',
                peer_review_id, grader_id, target_problem_id, challenge_end_time, class_id, enum.RoleType.normal,
            )
            return peer_review_record_id

        else:
            raise ValueError(f'Unknown {selection_type=}')
