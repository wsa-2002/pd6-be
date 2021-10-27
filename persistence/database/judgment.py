from typing import Sequence, Tuple
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


async def browse_latest_with_submission_ids(submission_ids: list[int]) -> Sequence[do.Judgment]:
    cond_sql = '), ('.join(str(submission_id) for submission_id in submission_ids)
    async with SafeExecutor(
            event='browse judgments with submission ids',
            sql=fr'SELECT judgment.id, judgment.submission_id, judgment.verdict,'
                fr'       judgment.total_time, judgment.max_memory, judgment.score, judgment.judge_time'
                fr'  FROM (VALUES ({cond_sql}))'
                fr'    AS from_submission(id)'
                fr' INNER JOIN judgment'
                fr'    ON from_submission.id = judgment.submission_id'
                fr'   AND submission_last_judgment_id(from_submission.id) = judgment.id',
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
            sql=fr'INSERT INTO judge_case (judgment_id, testcase_id, verdict, time_lapse, peak_memory, score)'
                fr'     VALUES (%(judgment_id)s, %(testcase_id)s, %(verdict)s,'
                fr'             %(time_lapse)s, %(peak_memory)s, %(score)s)',
            judgment_id=judgment_id, testcase_id=testcase_id, verdict=verdict,
            time_lapse=time_lapse, peak_memory=peak_memory, score=score,
    ):
        pass


async def read_by_challenge_type(problem_id: int, account_id: int,
                                 selection_type: enum.TaskSelectionType,
                                 challenge_end_time: datetime) -> do.Judgment:
    is_last = selection_type is enum.TaskSelectionType.last
    order_criteria = 'submission.submit_time DESC, submission.id DESC' if is_last else 'judgment.score DESC'
    async with SafeExecutor(
            event='get submission score by LAST',
            sql=fr'SELECT judgment.id, judgment.submission_id, judgment.verdict, judgment.total_time,'
                fr'       judgment.max_memory, judgment.score, judgment.judge_time'
                fr'  FROM submission'
                fr' INNER JOIN judgment'
                fr'         ON submission.id = judgment.submission_id'
                fr'        AND submission_last_judgment_id(submission.id) = judgment.id'
                fr' WHERE submission.account_id = %(account_id)s'
                fr'   AND submission.submit_time <= %(challenge_end_time)s'
                fr'   AND submission.problem_id = %(problem_id)s'
                fr' ORDER BY {order_criteria}'
                fr' LIMIT 1',
            account_id=account_id, challenge_end_time=challenge_end_time, problem_id=problem_id,
            fetch=1,
    ) as (id_, submission_id, verdict, total_time, max_memory, score, judge_time):
        return do.Judgment(id=id_, submission_id=submission_id, verdict=enum.VerdictType(verdict),
                           total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)


async def get_best_submission_judgment_all_time(problem_id: int, account_id: int) -> do.Judgment:
    async with SafeExecutor(
            event='get best submission judgment by all time',
            sql=fr'SELECT judgment.id, judgment.submission_id, judgment.verdict, judgment.total_time,'
                fr'       judgment.max_memory, judgment.score, judgment.judge_time'
                fr'  FROM submission'
                fr' INNER JOIN judgment'
                fr'         ON submission.id = judgment.submission_id'
                fr'        AND submission_last_judgment_id(submission.id) = judgment.id'
                fr' WHERE submission.account_id = %(account_id)s'
                fr'   AND submission.problem_id = %(problem_id)s'
                fr' ORDER BY judgment.score DESC'
                fr' LIMIT 1',
            account_id=account_id, problem_id=problem_id,
            fetch=1,
    ) as (id_, submission_id, verdict, total_time, max_memory, score, judge_time):
        return do.Judgment(id=id_, submission_id=submission_id, verdict=verdict, total_time=total_time,
                           max_memory=max_memory, score=score, judge_time=judge_time)


async def browse_by_problem_class_members(problem_id: int, selection_type: enum.TaskSelectionType) \
        -> dict[int, do.Judgment]:
    """
    Returns only submitted & judged members

    :return: member_id, judgment
    """

    order_criteria = 'submission.submit_time DESC, submission.id DESC' \
        if selection_type == enum.TaskSelectionType.last \
        else 'judgment.score DESC, submission.id DESC'

    async with SafeExecutor(
            event='browse judgment by problem class members',
            sql=fr'SELECT DISTINCT ON (class_member.member_id)'
                fr'       class_member.member_id,'
                fr'       judgment.id, judgment.submission_id, judgment.verdict,'
                fr'       judgment.total_time, judgment.max_memory, judgment.score, judgment.judge_time'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON challenge.class_id = class_member.class_id'
                fr'        AND NOT challenge.is_deleted'
                fr' INNER JOIN problem'
                fr'         ON problem.challenge_id = challenge.id'
                fr'        AND NOT problem.is_deleted'
                fr'        AND problem.id = %(problem_id)s'
                fr' INNER JOIN submission'
                fr'         ON submission.problem_id = problem.id'
                fr'        AND submission.account_id = class_member.member_id'
                fr'        AND submission.submit_time <= challenge.end_time'
                fr' INNER JOIN judgment'
                fr'         ON judgment.submission_id = submission.id'
                fr'        AND judgment.id = submission_last_judgment_id(submission.id)'
                fr' ORDER BY class_member.member_id, {order_criteria}',
            problem_id=problem_id,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return {member_id: do.Judgment(id=judgment_id, submission_id=submission_id, verdict=verdict,
                                       total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time)
                for member_id, judgment_id, submission_id, verdict, total_time, max_memory, score, judge_time
                in records}


async def get_class_last_team_submission_judgment(problem_id: int, class_id: int, team_ids: Sequence[int]) \
    -> Tuple[dict[int, do.Submission], dict[int, do.Judgment]]:
    cond_sql = ', '.join(str(team_id) for team_id in team_ids)
    async with SafeExecutor(
            event='get class last team submission judgment',
            sql=fr'  WITH data_table AS ( '
                fr'SELECT team_member.team_id          AS team_id,'
                fr'       submission.id                AS submission_id,'
                fr'       submission.account_id        AS account_id,'
                fr'       submission.problem_id        AS problem_id,'
                fr'       submission.language_id       AS language_id,'
                fr'       submission.content_length    AS content_length,'
                fr'       submission.submit_time       AS submit_time,'
                fr'       submission.content_file_uuid AS content_file_uuid,'
                fr'       submission.filename          AS filename,'
                fr'       judgment.id                  AS judgment_id,'
                fr'       judgment.submission_id       AS judgment_submission_id,'
                fr'       judgment.verdict             AS verdict,'
                fr'       judgment.total_time          AS total_time,'
                fr'       judgment.max_memory          AS max_memory,'
                fr'       judgment.score               AS score,'
                fr'       judgment.judge_time          AS judge_time'
                fr'  FROM team_member'
                fr' INNER JOIN team'
                fr'         ON team.id = team_member.team_id'
                fr'        AND team.class_id = %(class_id)s'
                fr'        AND team.id IN ({cond_sql})'
                fr'        AND NOT team.is_deleted'
                fr' INNER JOIN submission'
                fr'         ON team_member.member_id = submission.account_id'
                fr'        AND submission.problem_id = %(problem_id)s'
                fr' INNER JOIN problem'
                fr'         ON problem.id = submission.problem_id'
                fr' INNER JOIN challenge'
                fr'         ON challenge.id = problem.challenge_id'
                fr'        AND submission.submit_time <= challenge.end_time'
                fr' INNER JOIN judgment'
                fr'         ON submission.id = judgment.submission_id'
                fr'        AND submission_last_judgment_id(submission.id) = judgment.id'
                fr') '
                fr' SELECT t1.*'
                fr'   FROM data_table t1'
                fr'   LEFT JOIN data_table t2'
                fr'          ON t1.team_id = t2.team_id'
                fr'         AND (t1.submit_time < t2.submit_time OR '
                fr'             (t1.submit_time = t2.submit_time AND t1.submission_id < t2.submission_id))'
                fr' WHERE t2.submit_time IS NULL',
            class_id=class_id, problem_id=problem_id,
            fetch='all',
    ) as records:
        return ({team_id: do.Submission(id=submission_id, account_id=account_id, problem_id=problem_id,
                                       language_id=language_id, content_length=content_length, submit_time=submit_time,
                                       content_file_uuid=content_file_uuid, filename=filename)
                for team_id, submission_id, account_id, problem_id, language_id, content_length, submit_time,
                    content_file_uuid, filename, judgment_id, judgment_submission_id, verdict, total_time, max_memory, score, judge_time
                in records},
               {team_id: do.Judgment(id=judgment_id, submission_id=judgment_submission_id, verdict=verdict, total_time=total_time,
                                     max_memory=max_memory, score=score, judge_time=judge_time)
                for team_id, submission_id, account_id, problem_id, language_id, content_length, submit_time,
                    content_file_uuid, filename, judgment_id, judgment_submission_id, verdict, total_time, max_memory, score, judge_time
                in records})

