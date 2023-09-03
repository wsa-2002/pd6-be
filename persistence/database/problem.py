from typing import Optional, Sequence, Tuple
from datetime import datetime

from base import do, enum
from util import serialize

from . import testcase
from .base import AutoTxConnection, FetchOne, OnlyExecute, FetchAll, ParamDict


async def add(challenge_id: int, challenge_label: str,
              title: str, setter_id: int, full_score: Optional[int], description: Optional[str],
              io_description: Optional[str], source: Optional[str], hint: Optional[str],
              judge_type: Optional[enum.ProblemJudgeType] = enum.ProblemJudgeType.normal) -> int:
    async with FetchOne(
            event='Add problem',
            sql="INSERT INTO problem"
                "            (challenge_id, challenge_label, judge_type,"
                "             title, setter_id, full_score, description, io_description,"
                "             source, hint)"
                "     VALUES (%(challenge_id)s, %(challenge_label)s, %(judge_type)s,"
                "             %(title)s, %(setter_id)s, %(full_score)s, %(description)s, %(io_description)s,"
                "             %(source)s, %(hint)s)"
                "  RETURNING id",
            challenge_id=challenge_id, challenge_label=challenge_label, judge_type=judge_type,
            title=title, setter_id=setter_id, full_score=full_score,
            description=description, io_description=io_description,
            source=source, hint=hint,
    ) as (id_,):
        return id_


async def browse(include_scheduled: bool = False, include_deleted=False) -> Sequence[do.Problem]:
    filters = []

    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(filters)

    async with FetchAll(
            event='browse problems',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, full_score, judge_type, setting_id,'
                fr'       reviser_settings, description, io_description, source, hint, is_deleted, is_lazy_judge'
                fr'  FROM problem'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           title=title, setter_id=setter_id, full_score=full_score,
                           judge_type=enum.ProblemJudgeType(judge_type), setting_id=setting_id,
                           reviser_settings=serialize.unmarshal(reviser_settings, list[do.ProblemReviserSetting]),
                           description=description, io_description=io_description, source=source, hint=hint,
                           is_deleted=is_deleted, is_lazy_judge=is_lazy_judge)
                for (id_, challenge_id, challenge_label, title, setter_id, full_score, judge_type, setting_id,
                     reviser_settings, description, io_description, source, hint, is_deleted, is_lazy_judge)
                in records]


async def browse_problem_set(request_time: datetime, include_deleted=False) \
        -> Sequence[do.Problem]:
    async with FetchAll(
            event='browse problem set',
            sql=fr'SELECT problem.id, problem.challenge_id, problem.challenge_label,'
                fr'       problem.title, problem.setter_id, problem.full_score,'
                fr'       problem.description, problem.io_description, problem.judge_type, problem.setting_id,'
                fr'       problem.reviser_settings, problem.source, problem.hint, problem.is_deleted, '
                fr'       problem.is_lazy_judge'
                fr'  FROM problem'
                fr'       INNER JOIN challenge'
                fr'               ON challenge.id = problem.challenge_id'
                fr' WHERE challenge.publicize_type = %(start_time)s AND challenge.start_time <= %(request_time)s'
                fr'    OR challenge.publicize_type = %(end_time)s AND challenge.end_time <= %(request_time)s'
                fr'{" AND NOT problem.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY problem.id ASC',
            request_time=request_time,
            start_time=enum.ChallengePublicizeType.start_time,
            end_time=enum.ChallengePublicizeType.end_time,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           title=title, setter_id=setter_id, full_score=full_score,
                           description=description, io_description=io_description,
                           judge_type=enum.ProblemJudgeType(judge_type), setting_id=setting_id,
                           reviser_settings=serialize.unmarshal(reviser_settings, list[do.ProblemReviserSetting]),
                           source=source, hint=hint,
                           is_deleted=is_deleted, is_lazy_judge=is_lazy_judge)
                for (id_, challenge_id, challenge_label, title, setter_id, full_score,
                     description, io_description, judge_type, setting_id, reviser_settings,
                     source, hint, is_deleted, is_lazy_judge)
                in records]


async def browse_by_challenge(challenge_id: int, include_deleted=False) -> Sequence[do.Problem]:
    async with FetchAll(
            event='browse problems with challenge id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, full_score, judge_type, setting_id,'
                fr'       reviser_settings, description, io_description, source, hint, is_deleted, is_lazy_judge'
                fr'  FROM problem'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            challenge_id=challenge_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           title=title, setter_id=setter_id, full_score=full_score,
                           judge_type=enum.ProblemJudgeType(judge_type), setting_id=setting_id,
                           reviser_settings=serialize.unmarshal(reviser_settings, list[do.ProblemReviserSetting]),
                           description=description, io_description=io_description, source=source, hint=hint,
                           is_deleted=is_deleted, is_lazy_judge=is_lazy_judge)
                for (id_, challenge_id, challenge_label, title, setter_id, full_score, judge_type, setting_id,
                     reviser_settings, description, io_description, source, hint, is_deleted, is_lazy_judge)
                in records]


async def read(problem_id: int, include_deleted=False) -> do.Problem:
    async with FetchOne(
            event='read problem by id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, full_score,'
                fr'       judge_type, setting_id, reviser_settings,'
                fr'       description, io_description, source, hint, is_deleted, is_lazy_judge'
                fr'  FROM problem'
                fr' WHERE id = %(problem_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            problem_id=problem_id,
    ) as (id_, challenge_id, challenge_label, title, setter_id, full_score, judge_type,
          setting_id, reviser_settings, description, io_description, source, hint, is_deleted, is_lazy_judge):
        return do.Problem(id=id_,
                          challenge_id=challenge_id, challenge_label=challenge_label,
                          title=title, setter_id=setter_id, full_score=full_score,
                          judge_type=enum.ProblemJudgeType(judge_type), setting_id=setting_id,
                          reviser_settings=serialize.unmarshal(reviser_settings, list[do.ProblemReviserSetting]),
                          description=description, io_description=io_description, source=source, hint=hint,
                          is_deleted=is_deleted, is_lazy_judge=is_lazy_judge)


async def read_task_status_by_type(problem_id: int, account_id: int,
                                   selection_type: enum.TaskSelectionType,
                                   challenge_end_time: datetime, include_deleted=False) \
        -> Tuple[do.Problem, do.Submission]:
    is_last = selection_type is enum.TaskSelectionType.last
    async with FetchOne(
            event='read problem submission verdict by task selection type',
            sql=fr'SELECT problem.id, problem.challenge_id, problem.challenge_label, problem.title,'
                fr'       problem.setter_id, problem.full_score,'
                fr'       problem.judge_type, problem.setting_id, problem.reviser_settings,'
                fr'       problem.description, problem.io_description,'
                fr'       problem.source, problem.hint, problem.is_deleted, is_lazy_judge,'
                fr'       submission.id, submission.account_id, submission.problem_id,'
                fr'       submission.language_id, submission.filename,'
                fr'       submission.content_file_uuid, submission.content_length, submission.submit_time'
                fr'  FROM problem'
                fr' INNER JOIN submission'
                fr'         ON submission.problem_id = problem.id'
                fr' INNER JOIN judgment'
                fr'         ON judgment.submission_id = submission.id'
                fr' WHERE problem.id = %(problem_id)s'
                fr'   AND submission.submit_time <= %(challenge_end_time)s'
                fr'   AND submission.account_id = %(account_id)s'
                fr'{" AND NOT problem.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY '
                fr'{"submission.submit_time" if is_last else "judgment.verdict, judgment.score"} DESC'
                fr' LIMIT 1',
            problem_id=problem_id,
            challenge_end_time=challenge_end_time,
            account_id=account_id,
    ) as (problem_id, challenge_id, challenge_label, title, setter_id, full_score, judge_type,
          setting_id, reviser_settings, description, io_description, source, hint, is_deleted, is_lazy_judge,
          submission_id, account_id, problem_id, language_id, filename, content_file_uuid, content_length, submit_time):
        return (do.Problem(id=problem_id, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                           setter_id=setter_id, full_score=full_score,
                           judge_type=enum.ProblemJudgeType(judge_type), setting_id=setting_id,
                           reviser_settings=serialize.unmarshal(reviser_settings, list[do.ProblemReviserSetting]),
                           description=description, io_description=io_description, source=source,
                           hint=hint, is_deleted=is_deleted, is_lazy_judge=is_lazy_judge),
                do.Submission(id=submission_id, account_id=account_id, problem_id=problem_id, filename=filename,
                              language_id=language_id, content_file_uuid=content_file_uuid,
                              content_length=content_length, submit_time=submit_time))


async def edit(problem_id: int,
               judge_type: enum.ProblemJudgeType,
               challenge_label: str = None,
               title: str = None,
               setting_id: Optional[int] = ...,
               reviser_settings: Optional[Sequence[do.ProblemReviserSetting]] = ...,
               full_score: Optional[int] = ...,
               description: Optional[str] = ...,
               io_description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,
               is_lazy_judge: Optional[bool] = None,) -> None:
    to_updates: ParamDict = {'judge_type': judge_type}

    if challenge_label is not None:
        to_updates['challenge_label'] = challenge_label
    if title is not None:
        to_updates['title'] = title
    if setting_id is not ...:
        to_updates['setting_id'] = setting_id
    if reviser_settings is not ...:
        to_updates['reviser_settings'] = serialize.marshal(reviser_settings)
    if full_score is not ...:
        to_updates['full_score'] = full_score
    if description is not ...:
        to_updates['description'] = description
    if io_description is not ...:
        to_updates['io_description'] = io_description
    if source is not ...:
        to_updates['source'] = source
    if hint is not ...:
        to_updates['hint'] = hint
    if is_lazy_judge is not None:
        to_updates['is_lazy_judge'] = is_lazy_judge

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='edit problem',
            sql=fr'UPDATE problem'
                fr'   SET {set_sql}'
                fr' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            **to_updates,
    ):
        pass


async def delete(problem_id: int) -> None:
    async with OnlyExecute(
            event='soft delete problem',
            sql=r'UPDATE problem'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            is_deleted=True,
    ):
        pass


async def delete_cascade(problem_id: int) -> None:
    async with AutoTxConnection(event=f'cascade delete from problem {problem_id}') as conn:
        await testcase.delete_cascade_from_problem(problem_id=problem_id, cascading_conn=conn)

        await conn.execute(r'UPDATE problem'
                           r'   SET is_deleted = $1'
                           r' WHERE id = $2',
                           True, problem_id)


async def delete_cascade_from_challenge(challenge_id: int, cascading_conn=None) -> None:
    if cascading_conn:
        await _delete_cascade_from_challenge(challenge_id, conn=cascading_conn)
        return

    async with AutoTxConnection(event=f'cascade delete problem from challenge {challenge_id=}') as conn:
        await _delete_cascade_from_challenge(challenge_id, conn=conn)


async def _delete_cascade_from_challenge(challenge_id: int, conn) -> None:
    await conn.execute(r'UPDATE problem'
                       r'   SET is_deleted = $1'
                       r' WHERE challenge_id = $2',
                       True, challenge_id)


# === statistics


async def class_total_ac_member_count(problem_id: int) -> int:
    async with FetchOne(
            event='get total ACCEPTED member count by problem',
            sql=r'SELECT count(DISTINCT class_member.member_id)'
                r'  FROM class_member'
                r' INNER JOIN submission'
                r'         ON submission.account_id = class_member.member_id'
                r' INNER JOIN judgment'
                r'         ON judgment.submission_id = submission.id'
                r'        AND submission_last_judgment_id(submission.id) = judgment.id'
                r'        AND judgment.verdict = %(judgment_verdict)s'
                r' INNER JOIN problem'
                r'         ON problem.id = submission.problem_id'
                r' INNER JOIN challenge'
                r'         ON challenge.id = problem.challenge_id'
                r'        AND challenge.class_id = class_member.class_id'
                r'        AND submission.submit_time <= challenge.end_time'
                r'        AND NOT challenge.is_deleted'
                r' WHERE class_member.role = %(role)s'
                r'   AND submission.problem_id = %(problem_id)s',
            judgment_verdict=enum.VerdictType.accepted, role=enum.RoleType.normal,
            problem_id=problem_id,
    ) as (count,):
        return count


async def total_ac_member_count(problem_id: int) -> int:
    async with FetchOne(
            event='get total ACCEPTED member count by problem',
            sql=r'SELECT COUNT(DISTINCT submission.account_id)'
                r'  FROM submission'
                r' INNER JOIN judgment'
                r'         ON submission.id = judgment.submission_id'
                r'        AND submission_last_judgment_id(submission.id) = judgment.id'
                r'        AND judgment.verdict = %(judgment_verdict)s'
                r' INNER JOIN problem'
                r'         ON problem.id = submission.problem_id'
                r'        AND NOT problem.is_deleted'
                r' INNER JOIN challenge'
                r'         ON challenge.id = problem.challenge_id'
                r'        AND submission.submit_time <= challenge.end_time'
                r'        AND NOT challenge.is_deleted'
                r' WHERE submission.problem_id = %(problem_id)s',
            judgment_verdict=enum.VerdictType.accepted,
            problem_id=problem_id,
    ) as (count,):
        return count


async def class_total_submission_count(problem_id: int, challenge_id: int) -> int:
    async with FetchOne(
            event='get total submission count by problem',
            sql=r'SELECT count(*)'
                r'  FROM submission'
                r' INNER JOIN class_member'
                r'         ON class_member.member_id = submission.account_id'
                r'        AND class_member.role = %(role)s'
                r' INNER JOIN challenge'
                r'         ON class_member.class_id = challenge.class_id'
                r'        AND submission.submit_time <= challenge.end_time'
                r'        AND challenge.id = %(challenge_id)s'
                r'        AND NOT challenge.is_deleted'
                r' WHERE submission.problem_id = %(problem_id)s',
            role=enum.RoleType.normal, problem_id=problem_id, challenge_id=challenge_id,
    ) as (count,):
        return count


async def total_submission_count(problem_id: int) -> int:
    async with FetchOne(
            event='get total submission count by problem',
            sql=r'SELECT count(*)'
                r'  FROM submission'
                r' INNER JOIN problem'
                r'         ON submission.problem_id = problem.id'
                r'        AND NOT problem.is_deleted'
                r' INNER JOIN challenge'
                r'         ON problem.challenge_id = challenge.id'
                r'        AND submission.submit_time <= challenge.end_time'
                r'        AND NOT challenge.is_deleted'
                r' WHERE submission.problem_id = %(problem_id)s',
            problem_id=problem_id,
    ) as (count,):
        return count


async def class_total_member_count(problem_id: int) -> int:
    async with FetchOne(
            event='get total member count by problem',
            sql=r'SELECT count(distinct class_member.member_id)'
                r'  FROM class_member'
                r' INNER JOIN submission'
                r'         ON submission.account_id = class_member.member_id'
                r' INNER JOIN problem'
                r'         ON problem.id = submission.problem_id'
                r'        AND NOT problem.is_deleted'
                r' INNER JOIN challenge'
                r'         ON problem.challenge_id = challenge.id'
                r'        AND challenge.class_id = class_member.class_id'
                r'        AND submission.submit_time <= challenge.end_time'
                r'        AND NOT challenge.is_deleted'
                r' WHERE class_member.role = %(role)s'
                r'   AND submission.problem_id = %(problem_id)s',
            role=enum.RoleType.normal, problem_id=problem_id,
    ) as (count,):
        return count


async def total_member_count(problem_id: int) -> int:
    async with FetchOne(
            event='get total member count by problem',
            sql=r'SELECT count(distinct submission.account_id)'
                r'  FROM submission'
                r' INNER JOIN problem'
                r'         ON problem.id = submission.problem_id'
                r'        AND NOT problem.is_deleted'
                r' INNER JOIN challenge'
                r'         ON problem.challenge_id = challenge.id'
                r'        AND submission.submit_time <= challenge.end_time'
                r'        AND NOT challenge.is_deleted'
                r' WHERE submission.problem_id = %(problem_id)s',
            problem_id=problem_id,
    ) as (count,):
        return count
