from datetime import datetime
from typing import Sequence
from uuid import UUID

from base import do, enum
from base.popo import Filter, Sorter

from .base import FetchAll, FetchOne, OnlyExecute, ParamDict
from .util import execute_count, compile_filters


# Submission Language


async def add_language(name: str, version: str, queue_name: str, is_disabled: bool) -> int:
    async with FetchOne(
            event='Add submission language',
            sql="INSERT INTO submission_language"
                "            (name, version, queue_name, is_disabled)"
                "     VALUES (%(name)s, %(version)s, %(queue_name)s, %(is_disabled)s)"
                "  RETURNING id",
            name=name, version=version, queue_name=queue_name, is_disabled=is_disabled,
    ) as (id_,):
        return id_


async def edit_language(language_id: int,
                        name: str = None, version: str = None, is_disabled: bool = None) -> None:
    to_updates: ParamDict = {}

    if name is not None:
        to_updates['name'] = name
    if version is not None:
        to_updates['version'] = version
    if is_disabled is not ...:
        to_updates['is_disabled'] = is_disabled

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='edit submission language',
            sql=fr'UPDATE submission_language'
                fr'   SET {set_sql}'
                fr' WHERE id = %(language_id)s',
            language_id=language_id,
            **to_updates,
    ):
        pass


async def browse_language(include_disabled=True) -> Sequence[do.SubmissionLanguage]:
    async with FetchAll(
            event='Browse submission language',
            sql=fr'SELECT id, name, version, is_disabled'
                fr'  FROM submission_language'
                fr'{" WHERE NOT is_disabled" if not include_disabled else ""}'
                fr' ORDER BY name ASC, version ASC',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.SubmissionLanguage(id=id_, name=name, version=version, is_disabled=is_disabled)
                for id_, name, version, is_disabled in records]


async def read_language(language_id: int, include_disabled=True) -> do.SubmissionLanguage:
    async with FetchOne(
            event='read submission language',
            sql=fr'SELECT id, name, version, is_disabled'
                fr'  FROM submission_language'
                fr' WHERE id = %(id)s'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}',
            id=language_id,
    ) as (id_, name, version, is_disabled):
        return do.SubmissionLanguage(id=id_, name=name, version=version, is_disabled=is_disabled)


async def read_language_queue_name(language_id: int, include_disabled=True) -> str:
    async with FetchOne(
            event='read submission language queue name',
            sql=fr'SELECT queue_name'
                fr'  FROM submission_language'
                fr' WHERE id = %(id)s'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}',
            id=language_id,
    ) as (queue_name,):
        return queue_name


# Submission


async def add(account_id: int, problem_id: int, language_id: int,
              content_file_uuid: UUID, filename: str, content_length: int, submit_time: datetime) -> int:
    async with FetchOne(
            event='Add submission',
            sql="INSERT INTO submission"
                "            (account_id, problem_id, language_id, filename,"
                "             content_file_uuid, content_length, submit_time)"
                "     VALUES (%(account_id)s, %(problem_id)s, %(language_id)s, %(filename)s,"
                "             %(content_file_uuid)s, %(content_length)s, %(submit_time)s)"
                "  RETURNING id",
            account_id=account_id, problem_id=problem_id, language_id=language_id, filename=filename,
            content_file_uuid=content_file_uuid, content_length=content_length, submit_time=submit_time,
    ) as (id_,):
        return id_


async def edit(submission_id: int, content_file_uuid: UUID, content_length: int, filename: str):
    to_updates: ParamDict = {
        'content_file_uuid': content_file_uuid,
        'content_length': content_length,
        'filename': filename,
    }

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='add file id and length',
            sql=fr'UPDATE submission'
                fr'   SET {set_sql}'
                fr' WHERE id  = %(submission_id)s',
            submission_id=submission_id,
            **to_updates,
    ):
        pass


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[do.Submission], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse submissions',
            sql=fr'SELECT id, account_id, problem_id, language_id, filename,'
                fr'       content_file_uuid, content_length, submit_time'
                fr'  FROM submission'
                fr' {f"WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} id DESC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.Submission(id=id_, account_id=account_id, problem_id=problem_id, language_id=language_id,
                              filename=filename, content_file_uuid=content_file_uuid, content_length=content_length,
                              submit_time=submit_time)
                for id_, account_id, problem_id, language_id, filename, content_file_uuid, content_length, submit_time
                in records]

    total_count = await execute_count(
        sql=fr'SELECT id, account_id, problem_id, language_id, filename,'
            fr'       content_file_uuid, content_length, submit_time'
            fr'  FROM submission'
            fr' {f"WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def read(submission_id: int) -> do.Submission:
    async with FetchOne(
            event='read submission',
            sql=r'SELECT account_id, problem_id, language_id, filename,'
                r'       content_file_uuid, content_length, submit_time'
                r'  FROM submission'
                r' WHERE id = %(submission_id)s',
            submission_id=submission_id,
    ) as (account_id, problem_id, language_id, filename, content_file_uuid, content_length, submit_time):
        return do.Submission(id=submission_id, account_id=account_id, problem_id=problem_id, filename=filename,
                             language_id=language_id, content_file_uuid=content_file_uuid,
                             content_length=content_length, submit_time=submit_time)


async def read_latest_judgment(submission_id: int) -> do.Judgment:
    async with FetchOne(
            event='read submission latest judgment',
            sql=r'SELECT judgment.id, judgment.submission_id, judgment.verdict, judgment.total_time,'
                r'       judgment.max_memory, judgment.score, judgment.judge_time, judgment.error_message' 
                r'  FROM judgment'
                r' INNER JOIN submission'
                r'         ON submission.id = judgment.submission_id'
                r' WHERE submission.id = %(submission_id)s'
                r' ORDER BY judgment.id DESC'
                r' LIMIT 1',
            submission_id=submission_id,
    ) as (judgment_id, submission_id, verdict, total_time, max_memory, score, judge_time, error_message):
        return do.Judgment(id=judgment_id, submission_id=submission_id, verdict=enum.VerdictType(verdict),
                           total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time,
                           error_message=error_message)


async def browse_under_class(class_id: int,
                             limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[do.Submission], int]:

    filters = [Filter(col_name=f'submission.{filter_.col_name}',
                      op=filter_.op,
                      value=filter_.value) for filter_ in filters]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"submission.{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse submissions',
            sql=fr'SELECT submission.id, submission.account_id, submission.problem_id , submission.language_id, '
                fr'       submission.filename, submission.content_file_uuid, submission.content_length, submission.submit_time'
                fr'  FROM submission'
                fr'  INNER JOIN problem'
                fr'          ON problem.id = submission.problem_id'
                fr'         AND problem.is_deleted = %(problem_is_deleted)s'
                fr'  INNER JOIN challenge'
                fr'          ON challenge.id = problem.challenge_id '
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr'      AND challenge.class_id = %(class_id)s'
                fr' ORDER BY {sort_sql} submission.id DESC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            class_id=class_id, problem_is_deleted=False,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.Submission(id=id_, account_id=account_id, problem_id=problem_id, language_id=language_id,
                              filename=filename, content_file_uuid=content_file_uuid, content_length=content_length,
                              submit_time=submit_time)
                for id_, account_id, problem_id, language_id, filename, content_file_uuid, content_length, submit_time
                in records]

    total_count = await execute_count(
        sql=fr'SELECT submission.id, submission.account_id, submission.problem_id , submission.language_id, '
            fr'       submission.filename, submission.content_file_uuid, submission.content_length, submission.submit_time'
            fr'  FROM submission'
            fr'  INNER JOIN problem'
            fr'          ON problem.id = submission.problem_id'
            fr'         AND problem.is_deleted = %(problem_is_deleted)s'
            fr'  INNER JOIN challenge'
            fr'          ON challenge.id = problem.challenge_id '
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
            fr'      AND challenge.class_id = %(class_id)s',
        **cond_params, problem_is_deleted=False,
        class_id=class_id,
    )
    return data, total_count


async def browse_by_problem_selected(problem_id: int, selection_type: enum.TaskSelectionType, end_time: datetime) \
        -> Sequence[do.Submission]:
    """
    Returns only submitted & judged members

    :return: member_id, submission
    """

    if selection_type is enum.TaskSelectionType.last:
        order_criteria = 'submission.submit_time DESC'
        join_judgment_sql = ''
    elif selection_type is enum.TaskSelectionType.best:
        order_criteria = 'judgment.score DESC'
        join_judgment_sql = (r' INNER JOIN judgment'
                             r'         ON judgment.submission_id = submission.id'
                             r'        AND judgment.id = submission_last_judgment_id(submission.id)')
    else:
        raise ValueError(f'{selection_type} is not expected')

    async with FetchAll(
            event='browse submission by problem class members',
            sql=fr'SELECT DISTINCT ON (submission.account_id)'
                fr'       submission.id, submission.account_id, submission.problem_id , submission.language_id,'
                fr'       submission.filename, submission.content_file_uuid, submission.content_length,'
                fr'       submission.submit_time'
                fr'  FROM submission'
                fr'{join_judgment_sql if selection_type is enum.TaskSelectionType.best else ""}'
                fr' WHERE submission.problem_id = %(problem_id)s'
                fr'   AND submission.submit_time <= %(end_time)s'
                fr' ORDER BY submission.account_id, {order_criteria}, submission.id DESC',
            problem_id=problem_id, end_time=end_time,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Submission(id=id_, account_id=account_id, problem_id=problem_id, language_id=language_id,
                              filename=filename, content_file_uuid=content_file_uuid, content_length=content_length,
                              submit_time=submit_time)
                for (id_, account_id, problem_id, language_id, filename, content_file_uuid, content_length, submit_time)
                in records]
