from typing import Sequence

from base import do, enum

from .base import SafeExecutor


async def browse(submission_id: int) -> Sequence[do.Judgment]:
    async with SafeExecutor(
            event='browse judgments',
            sql=fr'SELECT id, status, total_time, max_memory, score, judge_time'
                fr'  FROM judgment'
                fr' WHERE submission_id = %(submission_id)s',
            submission_id=submission_id,
            fetch='all',
    ) as results:
        return [do.Judgment(id=id_, submission_id=submission_id, status=enum.JudgmentStatusType(status),
                            total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)
                for id_, status, total_time, max_memory, score, judge_time in results]


async def read(judgment_id: int) -> do.Judgment:
    async with SafeExecutor(
            event='browse judgments',
            sql=fr'SELECT submission_id, status, total_time, max_memory, score, judge_time'
                fr'  FROM judgment'
                fr' WHERE judgment_id = %(judgment_id)s',
            judgment_id=judgment_id,
            fetch=1,
    ) as (submission_id, status, total_time, max_memory, score, judge_time):
        return do.Judgment(id=judgment_id, submission_id=submission_id, status=enum.JudgmentStatusType(status),
                           total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)
