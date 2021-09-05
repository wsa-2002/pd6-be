from typing import Sequence
from datetime import datetime

from base import do, enum

from .base import SafeExecutor


async def browse(submission_id: int) -> Sequence[do.Judgment]:
    async with SafeExecutor(
            event='browse judgments',
            sql=fr'SELECT id, verdict, total_time, max_memory, score, judge_time'
                fr'  FROM judgment'
                fr' WHERE submission_id = %(submission_id)s'
                fr' ORDER BY id DESC',
            submission_id=submission_id,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Judgment(id=id_, submission_id=submission_id, verdict=enum.VerdictType(verdict),
                            total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)
                for id_, verdict, total_time, max_memory, score, judge_time in records]


async def browse_with_submission_ids(submission_ids: list[int]) -> Sequence[do.Judgment]:
    cond_sql = '), ('.join(str(submission_id) for submission_id in submission_ids)
    async with SafeExecutor(
            event='browse judgments with submission ids',
            sql=fr'SELECT DISTINCT ON (from_submission.id) judgment.*'
                fr'  FROM (VALUES ({cond_sql})) '
                fr'    AS from_submission(id)'
                fr' INNER JOIN judgment'
                fr'    ON from_submission.id = judgment.submission_id'
                fr' ORDER BY from_submission.id, judgment.judge_time DESC',
            fetch='all',
            raise_not_found=False,
    ) as records:
        return [do.Judgment(id=id_, submission_id=submission_id, verdict=enum.VerdictType(verdict),
                            total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)
                for (id_, submission_id, verdict, total_time, max_memory, score, judge_time) in records]


async def read(judgment_id: int) -> do.Judgment:
    async with SafeExecutor(
            event='read judgment',
            sql=fr'SELECT id, submission_id, verdict, total_time, max_memory, score, judge_time'
                fr'  FROM judgment'
                fr' WHERE id = %(judgment_id)s',
            judgment_id=judgment_id,
            fetch=1,
    ) as (id_, submission_id, verdict, total_time, max_memory, score, judge_time):
        return do.Judgment(id=id_, submission_id=submission_id, verdict=enum.VerdictType(verdict),
                           total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)


async def add(submission_id: int, verdict: enum.VerdictType, total_time: int, max_memory: int,
              score: int, judge_time: datetime) -> int:
    async with SafeExecutor(
            event='add judgment',
            sql=fr'INSERT INTO judgment (submission_id, verdict, total_time, max_memory, score, judge_time)'
                fr'     VALUES (%(submission_id)s, %(verdict)s, %(total_time)s,'
                fr'             %(max_memory)s, %(score)s, %(judge_time)s)'
                fr'  RETURNING id',
            submission_id=submission_id, verdict=verdict, total_time=total_time, max_memory=max_memory,
            score=score, judge_time=judge_time,
            fetch=1,
    ) as (judgment_id,):
        return judgment_id


async def browse_cases(judgment_id: int) -> Sequence[do.JudgeCase]:
    async with SafeExecutor(
            event='browse judge cases',
            sql=fr'SELECT judgment_id, testcase_id,'
                fr'       judge_case.verdict, judge_case.time_lapse, judge_case.peak_memory, judge_case.score'
                fr'  FROM judge_case'
                fr'       LEFT JOIN testcase'
                fr'              ON testcase.id = judge_case.testcase_id'
                fr' WHERE judgment_id = %(judgment_id)s'
                fr' ORDER BY testcase.is_sample DESC, testcase_id ASC',
            judgment_id=judgment_id,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.JudgeCase(judgment_id=judgment_id, testcase_id=testcase_id, verdict=enum.VerdictType(verdict),
                             time_lapse=time_lapse, peak_memory=peak_memory, score=score)
                for judgment_id, testcase_id, verdict, time_lapse, peak_memory, score in records]


async def read_case(judgment_id: int, testcase_id: int) -> do.JudgeCase:
    async with SafeExecutor(
            event='read judge case',
            sql=fr'SELECT judgment_id, testcase_id, verdict, time_lapse, peak_memory, score'
                fr'  FROM judge_case'
                fr' WHERE judgment_id = %(judgment_id)s and testcase_id = %(testcase_id)s',
            judgment_id=judgment_id,
            testcase_id=testcase_id,
            fetch=1,
    ) as (judgment_id, testcase_id, verdict, time_lapse, peak_memory, score):
        return do.JudgeCase(judgment_id=judgment_id, testcase_id=testcase_id, verdict=enum.VerdictType(verdict),
                            time_lapse=time_lapse, peak_memory=peak_memory, score=score)


async def add_case(judgment_id: int, testcase_id: int, verdict: enum.VerdictType,
                   time_lapse: int, peak_memory: int, score: int) -> None:
    async with SafeExecutor(
            event='add judge case',
            sql=fr'INSERT INTO judge_case (judgment_id, testcase_id, status, time_lapse, peak_memory, score)'
                fr'     VALUES (%(judgment_id)s, %(testcase_id)s, %(status)s,'
                fr'             %(time_lapse)s, %(peak_memory)s, %(score)s)',
            judgment_id=judgment_id, testcase_id=testcase_id, status=verdict,
            time_lapse=time_lapse, peak_memory=peak_memory, score=score,
    ):
        pass


async def get_submission_judgment_by_challenge_type(problem_id: int, account_id: int,
                                                    selection_type: enum.TaskSelectionType,
                                                    challenge_end_time: datetime) -> do.Judgment:
    is_last = selection_type is enum.TaskSelectionType.last
    async with SafeExecutor(
            event='get submission score by LAST',
            sql=fr'SELECT judgment.id, judgment.submission_id, judgment.verdict, judgment.total_time,'
                fr'       judgment.max_memory, judgment.score, judgment.judge_time'
                fr'  FROM judgment'
                fr' INNER JOIN submission'
                fr'         ON submission.id = judgment.submission_id'
                fr'        AND submission.account_id = %(account_id)s'
                fr'        AND submission.submit_time <= %(challenge_end_time)s'
                fr'        AND submission.problem_id = %(problem_id)s'
                fr' ORDER BY'
                fr' {"submission.id" if is_last else "judgment.score"}'
                fr' DESC'
                fr' LIMIT 1',
            account_id=account_id, challenge_end_time=challenge_end_time, problem_id=problem_id,
            fetch=1,
    ) as (id_, submission_id, verdict, total_time, max_memory, score, judge_time):
        return do.Judgment(id=id_, submission_id=submission_id, verdict=enum.JudgmentVerdictType(verdict),
                           total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)
