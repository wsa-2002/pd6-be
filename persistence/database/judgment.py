from typing import Sequence
from datetime import datetime

from base import do, enum

from .base import SafeExecutor


async def browse(submission_id: int) -> Sequence[do.Judgment]:
    async with SafeExecutor(
            event='browse judgments',
            sql=fr'SELECT id, status, total_time, max_memory, score, judge_time'
                fr'  FROM judgment'
                fr' WHERE submission_id = %(submission_id)s'
                fr' ORDER BY id DESC',
            submission_id=submission_id,
            fetch='all',
    ) as records:
        return [do.Judgment(id=id_, submission_id=submission_id, status=enum.JudgmentStatusType(status),
                            total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)
                for id_, status, total_time, max_memory, score, judge_time in records]


async def read(judgment_id: int) -> do.Judgment:
    async with SafeExecutor(
            event='read judgment',
            sql=fr'SELECT submission_id, status, total_time, max_memory, score, judge_time'
                fr'  FROM judgment'
                fr' WHERE judgment_id = %(judgment_id)s',
            judgment_id=judgment_id,
            fetch=1,
    ) as (submission_id, status, total_time, max_memory, score, judge_time):
        return do.Judgment(id=judgment_id, submission_id=submission_id, status=enum.JudgmentStatusType(status),
                           total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)


async def browse_cases(judgment_id: int) -> Sequence[do.JudgeCase]:
    async with SafeExecutor(
            event='browse judge cases',
            sql=fr'SELECT judgment_id, testcase_id,'
                fr'       judge_case.status, judge_case.time_lapse, judge_case.peak_memory, judge_case.score'
                fr'  FROM judge_case'
                fr'       LEFT JOIN testcase'
                fr'              ON testcase.id = judge_case.testcase_id'
                fr' WHERE judgment_id = %(judgment_id)s'
                fr' ORDER BY testcase.is_sample DESC, testcase_id ASC',
            judgment_id=judgment_id,
            fetch='all',
    ) as records:
        return [do.JudgeCase(judgment_id=judgment_id, testcase_id=testcase_id, status=enum.JudgmentStatusType(status),
                             time_lapse=time_lapse, peak_memory=peak_memory, score=score)
                for judgment_id, testcase_id, status, time_lapse, peak_memory, score in records]


async def read_case(judgment_id: int, testcase_id: int) -> do.JudgeCase:
    async with SafeExecutor(
            event='read judge case',
            sql=fr'SELECT judgment_id, testcase_id, status, time_lapse, peak_memory, score'
                fr'  FROM judge_case'
                fr' WHERE judgment_id = %(judgment_id)s and testcase_id = %(testcase_id)s',
            judgment_id=judgment_id,
            testcase_id=testcase_id,
            fetch=1,
    ) as (judgment_id, testcase_id, status, time_lapse, peak_memory, score):
        return do.JudgeCase(judgment_id=judgment_id, testcase_id=testcase_id, status=enum.JudgmentStatusType(status),
                            time_lapse=time_lapse, peak_memory=peak_memory, score=score)


async def get_submission_score(problem_id: int, account_id: int, selection_type: enum.TaskSelectionType,
                               challenge_end_time: datetime) -> do.Judgment:
    if selection_type is enum.TaskSelectionType.last:
        async with SafeExecutor(
                event='get submission score by LAST',
                sql=fr'SELECT judgment.id, judgment.submission_id, judgment.status, judgment.total_time,'
                    fr'       judgment.max_memory, judgment.score, judgment.judge_time'
                    fr'  FROM judgment'
                    fr' INNER JOIN submission'
                    fr'         ON submission.id = judgment.submission_id'
                    fr'        AND submission.account_id = %(account_id)s'
                    fr'        AND submission.submit_time <= %(challenge_end_time)s'
                    fr'        AND submission.problem_id = %(problem_id)s'
                    fr'   ORDER BY submission.id DESC'
                    fr' LIMIT 1',
                account_id=account_id, challenge_end_time=challenge_end_time, problem_id=problem_id,
                fetch=1,
        ) as (id_, submission_id, status, total_time, max_memory, score, judge_time):
            return do.Judgment(id=id_, submission_id=submission_id, status=status, total_time=total_time,
                               max_memory=max_memory, score=score, judge_time=judge_time)

    elif selection_type is enum.TaskSelectionType.best:
        async with SafeExecutor(
                event='get submission score by BEST',
                sql=fr'SELECT judgment.id, judgment.submission_id, judgment.status, judgment.total_time,'
                    fr'       judgment.max_memory, judgment.score, judgment.judge_time'
                    fr'  FROM judgment'
                    fr' INNER JOIN submission'
                    fr'         ON submission.id = judgment.submission_id'
                    fr'        AND submission.account_id = %(account_id)s'
                    fr'        AND submission.submit_time <= %(challenge_end_time)s'
                    fr'        AND submission.problem_id = %(problem_id)s'
                    fr' ORDER BY judgment.score DESC'
                    fr' LIMIT 1',
                account_id=account_id, challenge_end_time=challenge_end_time, problem_id=problem_id,
        ) as (id_, submission_id, status, total_time, max_memory, score, judge_time):
            return do.Judgment(id=id_, submission_id=submission_id, status=status, total_time=total_time,
                               max_memory=max_memory, score=score, judge_time=judge_time)
