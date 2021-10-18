from typing import Optional, Sequence, Tuple
from datetime import datetime

from base import do, enum

from . import testcase
from .base import SafeExecutor, SafeConnection


async def add(challenge_id: int, challenge_label: str,
              title: str, setter_id: int, full_score: Optional[int], description: Optional[str],
              io_description: Optional[str], source: Optional[str], hint: Optional[str]) -> int:
    async with SafeExecutor(
            event='Add problem',
            sql="INSERT INTO problem"
                "            (challenge_id, challenge_label,"
                "             title, setter_id, full_score, description, io_description,"
                "             source, hint)"
                "     VALUES (%(challenge_id)s, %(challenge_label)s,"
                "             %(title)s, %(setter_id)s, %(full_score)s, %(description)s, %(io_description)s,"
                "             %(source)s, %(hint)s)"
                "  RETURNING id",
            challenge_id=challenge_id, challenge_label=challenge_label,
            title=title, setter_id=setter_id, full_score=full_score,
            description=description, io_description=io_description,
            source=source, hint=hint,
            fetch=1,
    ) as (id_,):
        return id_


async def browse(include_scheduled: bool = False, include_deleted=False) -> Sequence[do.Problem]:
    filters = []

    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(filters)

    async with SafeExecutor(
            event='browse problems',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, full_score, '
                fr'       description, io_description, source, hint, is_deleted'
                fr'  FROM problem'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           title=title, setter_id=setter_id, full_score=full_score,
                           description=description, io_description=io_description, source=source, hint=hint,
                           is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, title, setter_id, full_score,
                     description, io_description, source, hint, is_deleted)
                in records]


async def browse_problem_set(request_time: datetime, include_deleted=False) \
        -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problem set',
            sql=fr'SELECT problem.id, problem.challenge_id, problem.challenge_label,'
                fr'       problem.title, problem.setter_id, problem.full_score, '
                fr'       problem.description, problem.io_description,'
                fr'       problem.source, problem.hint, problem.is_deleted'
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
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           title=title, setter_id=setter_id, full_score=full_score,
                           description=description, io_description=io_description, source=source, hint=hint,
                           is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, title, setter_id, full_score,
                     description, io_description, source, hint, is_deleted)
                in records]


async def browse_by_challenge(challenge_id: int, include_deleted=False) -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problems with challenge id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, full_score, '
                fr'       description, io_description, source, hint, is_deleted'
                fr'  FROM problem'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            challenge_id=challenge_id,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           title=title, setter_id=setter_id, full_score=full_score,
                           description=description, io_description=io_description, source=source, hint=hint,
                           is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, title, setter_id, full_score,
                     description, io_description, source, hint, is_deleted)
                in records]


async def read(problem_id: int, include_deleted=False) -> do.Problem:
    async with SafeExecutor(
            event='read problem by id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, full_score, '
                fr'       description, io_description, source, hint, is_deleted'
                fr'  FROM problem'
                fr' WHERE id = %(problem_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            problem_id=problem_id,
            fetch=1,
    ) as (id_, challenge_id, challenge_label, title, setter_id, full_score,
          description, io_description, source, hint, is_deleted):
        return do.Problem(id=id_,
                          challenge_id=challenge_id, challenge_label=challenge_label,
                          title=title, setter_id=setter_id, full_score=full_score,
                          description=description, io_description=io_description, source=source, hint=hint,
                          is_deleted=is_deleted)


async def read_task_status_by_type(problem_id: int, account_id: int,
                                   selection_type: enum.TaskSelectionType,
                                   challenge_end_time: datetime, include_deleted=False) \
        -> Tuple[do.Problem, do.Submission]:

    is_last = selection_type is enum.TaskSelectionType.last
    async with SafeExecutor(
            event='read problem submission verdict by task selection type',
            sql=fr'SELECT problem.id, problem.challenge_id, problem.challenge_label, problem.title,'
                fr'       problem.setter_id, problem.full_score, problem.description, problem.io_description,'
                fr'       problem.source, problem.hint, problem.is_deleted,'
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
            fetch=1,
    ) as (problem_id, challenge_id, challenge_label, title, setter_id, full_score,
          description, io_description, source, hint, is_deleted,
          submission_id, account_id, problem_id, language_id, filename, content_file_uuid, content_length, submit_time):
        return (do.Problem(id=problem_id, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                           setter_id=setter_id, full_score=full_score, description=description,
                           io_description=io_description, source=source, hint=hint, is_deleted=is_deleted),
                do.Submission(id=submission_id, account_id=account_id, problem_id=problem_id, filename=filename,
                              language_id=language_id, content_file_uuid=content_file_uuid,
                              content_length=content_length, submit_time=submit_time))


async def edit(problem_id: int,
               challenge_label: str = None,
               title: str = None,
               full_score: Optional[int] = ...,
               description: Optional[str] = ...,
               io_description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,) -> None:
    to_updates = {}

    if challenge_label is not None:
        to_updates['challenge_label'] = challenge_label
    if title is not None:
        to_updates['title'] = title
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

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit problem',
            sql=fr'UPDATE problem'
                fr'   SET {set_sql}'
                fr' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            **to_updates,
    ):
        pass


async def delete(problem_id: int) -> None:
    async with SafeExecutor(
            event='soft delete problem',
            sql=fr'UPDATE problem'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            is_deleted=True,
    ):
        pass


async def delete_cascade(problem_id: int) -> None:
    async with SafeConnection(event=f'cascade delete from problem {problem_id}') as conn:
        async with conn.transaction():
            await testcase.delete_cascade_from_problem(problem_id=problem_id, cascading_conn=conn)

            await conn.execute(fr'UPDATE problem'
                               fr'   SET is_deleted = $1'
                               fr' WHERE id = $2',
                               True, problem_id)


async def delete_cascade_from_challenge(challenge_id: int, cascading_conn=None) -> None:
    if cascading_conn:
        await _delete_cascade_from_challenge(challenge_id, conn=cascading_conn)
        return

    async with SafeConnection(event=f'cascade delete problem from challenge {challenge_id=}') as conn:
        async with conn.transaction():
            await _delete_cascade_from_challenge(challenge_id, conn=conn)


async def _delete_cascade_from_challenge(challenge_id: int, conn) -> None:
    await conn.execute(r'UPDATE problem'
                       r'   SET is_deleted = $1'
                       r' WHERE challenge_id = $2',
                       True, challenge_id)


# === statistics


# async def total_ac_member_count(problem_id: int) -> int:
#     async with SafeExecutor(
#             event='get total ACCEPTED member count by problem',
#             sql=fr'SELECT count(DISTINCT class_member.member_id)'
#                 fr'  FROM class_member'
#                 fr' INNER JOIN submission'
#                 fr'         ON submission.account_id = class_member.member_id'
#                 fr' INNER JOIN judgment'
#                 fr'         ON judgment.submission_id = submission.id'
#                 fr'        AND judgment.verdict = %(judgment_verdict)s'
#                 fr' INNER JOIN problem'
#                 fr'         ON problem.id = submission.problem_id'
#                 fr' INNER JOIN challenge'
#                 fr'         ON challenge.id = problem.challenge_id'
#                 fr'        AND challenge.class_id = class_member.class_id'
#                 fr'        AND submission.submit_time <= challenge.end_time'
#                 fr'        AND NOT challenge.is_deleted'
#                 fr' WHERE class_member.role = %(role)s'
#                 fr'   AND submission.problem_id = %(problem_id)s',
#             judgment_verdict=enum.VerdictType.accepted, role=enum.RoleType.normal,
#             problem_id=problem_id,
#             fetch=1,
#     ) as (count,):
#         return count


async def total_ac_member_count(problem_id: int) -> int:
    async with SafeExecutor(
            event='get total ACCEPTED member count by problem',
            sql=fr'SELECT COUNT(DISTINCT submission.account_id)'
                fr'  FROM submission'
                fr' INNER JOIN judgment'
                fr'         ON submission.id = judgment.submission_id'
                fr'        AND submission_last_judgment_id(submission.id) = judgment.id'
                fr'        AND judgment.verdict = %(judgment_verdict)s'
                fr' INNER JOIN problem'
                fr'         ON problem.id = submission.problem_id'
                fr'        AND NOT problem.is_deleted'
                fr' INNER JOIN challenge'
                fr'         ON challenge.id = problem.challenge_id'
                fr'        AND submission.submit_time <= challenge.end_time'
                fr'        AND NOT challenge.is_deleted'
                fr' WHERE submission.problem_id = %(problem_id)s',
            judgment_verdict=enum.VerdictType.accepted,
            problem_id=problem_id,
            fetch=1,
    ) as (count,):
        return count


# async def total_submission_count(problem_id: int, challenge_id: int) -> int:
#     async with SafeExecutor(
#             event='get total submission count by problem',
#             sql=fr'SELECT count(*)'
#                 fr'  FROM submission'
#                 fr' INNER JOIN class_member'
#                 fr'         ON class_member.member_id = submission.account_id'
#                 fr'        AND class_member.role = %(role)s'
#                 fr' INNER JOIN challenge'
#                 fr'         ON class_member.class_id = challenge.class_id'
#                 fr'        AND submission.submit_time <= challenge.end_time'
#                 fr'        AND challenge.id = %(challenge_id)s'
#                 fr'        AND NOT challenge.is_deleted'
#                 fr' WHERE submission.problem_id = %(problem_id)s',
#             role=enum.RoleType.normal, problem_id=problem_id, challenge_id=challenge_id,
#             fetch=1,
#     ) as (count,):
#         return count


async def total_submission_count(problem_id: int) -> int:
    async with SafeExecutor(
            event='get total submission count by problem',
            sql=fr'SELECT count(*)'
                fr'  FROM submission'
                fr' INNER JOIN problem'
                fr'         ON submission.problem_id = problem.id'
                fr'        AND NOT problem.is_deleted'
                fr' INNER JOIN challenge'
                fr'         ON problem.challenge_id = challenge.id'
                fr'        AND submission.submit_time <= challenge.end_time'
                fr'        AND NOT challenge.is_deleted'
                fr' WHERE submission.problem_id = %(problem_id)s',
            problem_id=problem_id,
            fetch=1,
    ) as (count,):
        return count


# async def total_member_count(problem_id: int) -> int:
#     async with SafeExecutor(
#             event='get total member count by problem',
#             sql=fr'SELECT count(distinct class_member.member_id)'
#                 fr'  FROM class_member'
#                 fr' INNER JOIN submission'
#                 fr'         ON submission.account_id = class_member.member_id'
#                 fr' INNER JOIN problem'
#                 fr'         ON problem.id = submission.problem_id'
#                 fr'        AND NOT problem.is_deleted'
#                 fr' INNER JOIN challenge'
#                 fr'         ON problem.challenge_id = challenge.id'
#                 fr'        AND challenge.class_id = class_member.class_id'
#                 fr'        AND submission.submit_time <= challenge.end_time'
#                 fr'        AND NOT challenge.is_deleted'
#                 fr' WHERE class_member.role = %(role)s'
#                 fr'   AND submission.problem_id = %(problem_id)s',
#             role=enum.RoleType.normal, problem_id=problem_id,
#             fetch=1,
#     ) as (count,):
#         return count


async def total_member_count(problem_id: int) -> int:
    async with SafeExecutor(
            event='get total member count by problem',
            sql=fr'SELECT count(distinct submission.account_id)'
                fr'  FROM submission'
                fr' INNER JOIN problem'
                fr'         ON problem.id = submission.problem_id'
                fr'        AND NOT problem.is_deleted'
                fr' INNER JOIN challenge'
                fr'         ON problem.challenge_id = challenge.id'
                fr'        AND submission.submit_time <= challenge.end_time'
                fr'        AND NOT challenge.is_deleted'
                fr' WHERE submission.problem_id = %(problem_id)s',
            problem_id=problem_id,
            fetch=1,
    ) as (count,):
        return count
