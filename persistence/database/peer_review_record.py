from datetime import datetime
from typing import Sequence

from base import do, enum
from base.popo import Filter, Sorter

from .base import SafeConnection, FetchAll, FetchOne, OnlyExecute
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
            sql=fr'SELECT id, peer_review_id, grader_id, receiver_id, score, comment, submit_time, submission_id'
                fr'  FROM peer_review_record'
                fr' WHERE id = %(peer_review_record_id)s',
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
    async with SafeConnection(event='add auto peer review record',
                              auto_transaction=True) as conn:
        (target_problem_id, challenge_end_time, raw_selection_type, class_id) = await conn.fetchrow(
            fr'SELECT peer_review.target_problem_id,'
            fr'       challenge.end_time, challenge.selection_type, challenge.class_id'
            fr'  FROM peer_review'
            fr'  LEFT JOIN problem'
            fr'         ON problem.id = peer_review.target_problem_id'
            fr'        AND NOT problem.is_deleted'
            fr'  LEFT JOIN challenge'
            fr'         ON challenge.id = problem.challenge_id'
            fr'        AND NOT challenge.is_deleted'
            fr' WHERE peer_review.id = $1',
            peer_review_id,
        )
        selection_type = enum.TaskSelectionType(raw_selection_type)

        if selection_type is enum.TaskSelectionType.last:
            (peer_review_record_id,) = await conn.fetchrow(
                fr'INSERT INTO peer_review_record'
                fr'            (peer_review_id, grader_id, receiver_id, submission_id)'
                fr'SELECT $1, $2, member_submission.member_id, member_submission.submission_id'
                fr'  FROM ('
                fr'       SELECT DISTINCT ON (cm.member_id)'
                fr'           cm.member_id AS member_id, submission.id AS submission_id'
                fr'         FROM class_member cm'
                fr'        INNER JOIN submission'
                fr'                ON cm.member_id = submission.account_id'
                fr'               AND submission.problem_id = $3'
                fr'               AND submission.submit_time <= $4'
                fr'        WHERE cm.class_id = $5'
                fr'          AND cm."role" = $6'
                fr'     ORDER BY cm.member_id, submission.id DESC'
                fr'     ) member_submission'
                fr'  LEFT JOIN ('
                fr'       SELECT cm.member_id AS member_id , count(*) AS count'
                fr'         FROM class_member cm'
                fr'        INNER JOIN peer_review_record prr'
                fr'                ON prr.receiver_id = cm.member_id'
                fr'               AND prr.peer_review_id = $1'
                fr'        WHERE cm.class_id = $5'
                fr'          AND cm."role" = $6'
                fr'     GROUP BY cm.member_id'
                fr'     ) prr_count'
                fr'    ON prr_count.member_id = member_submission.member_id'
                fr' WHERE member_submission.member_id != $2'
                fr' ORDER BY coalesce(prr_count.count, 0) ASC'
                fr' LIMIT 1'
                fr' RETURNING id',
                peer_review_id, grader_id, target_problem_id, challenge_end_time, class_id, enum.RoleType.normal,
            )
            return peer_review_record_id

        elif selection_type is enum.TaskSelectionType.best:
            (peer_review_record_id,) = await conn.fetchrow(
                fr'INSERT INTO peer_review_record'
                fr'            (peer_review_id, grader_id, receiver_id, submission_id)'
                fr'SELECT $1, $2, member_submission.member_id, member_submission.submission_id'
                fr'  FROM ('
                fr'       SELECT DISTINCT ON (cm.member_id)'
                fr'              cm.member_id AS member_id, submission_with_score.submission_id AS submission_id'
                fr'         FROM class_member cm'
                fr'        INNER JOIN ('
                fr'              SELECT DISTINCT ON (submission.id)'
                fr'                     submission.id AS submission_id, submission.account_id AS account_id,'
                fr'                     judgment.score AS score'
                fr'                FROM submission'
                fr'                LEFT JOIN judgment'
                fr'                       ON judgment.submission_id = submission.id'
                fr'               WHERE submission.problem_id = $3'
                fr'                 AND submission.submit_time <= $4'
                fr'            ORDER BY submission.id, judgment.judge_time DESC'
                fr'             ) submission_with_score'
                fr'            ON cm.member_id = submission_with_score.account_id'
                fr'         WHERE cm.class_id = $5'
                fr'           AND cm."role" = $6'
                fr'      ORDER BY cm.member_id, submission_with_score.score DESC'
                fr'     ) member_submission'
                fr'  LEFT JOIN ('
                fr'       SELECT cm.member_id AS member_id , count(*) AS count'
                fr'         FROM class_member cm'
                fr'        INNER JOIN peer_review_record prr'
                fr'                ON prr.receiver_id = cm.member_id'
                fr'               AND prr.peer_review_id = $1'
                fr'        WHERE cm.class_id = $5'
                fr'          AND cm."role" = $6'
                fr'     GROUP BY cm.member_id'
                fr'     ) prr_count'
                fr'    ON prr_count.member_id = member_submission.member_id'
                fr' WHERE member_submission.member_id != $2'
                fr' ORDER BY coalesce(prr_count.count, 0) ASC'
                fr' LIMIT 1'
                fr' RETURNING id',
                peer_review_id, grader_id, target_problem_id, challenge_end_time, class_id, enum.RoleType.normal,
            )
            return peer_review_record_id

        else:
            raise ValueError(f'Unknown {selection_type=}')
