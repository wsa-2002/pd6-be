from datetime import datetime
from typing import Optional, Sequence

import log
from base import do

from .base import SafeExecutor


# Submission Language


async def add_language(name: str, version: str, is_disabled: bool) -> int:
    async with SafeExecutor(
            event='Add submission language',
            sql="INSERT INTO submission_language"
                "            (name, version, is_disabled)"
                "     VALUES (%(name)s, %(version)s, %(is_disabled)s)"
                "  RETURNING id",
            name=name, version=version, is_disabled=is_disabled,
            fetch=1,
    ) as (id_,):
        return id_


async def edit_language(language_id: int,
                        name: str = None, version: str = None, is_disabled: bool = None) -> None:
    to_updates = {}

    if name is not None:
        to_updates['name'] = name
    if version is not None:
        to_updates['version'] = version
    if is_disabled is not ...:
        to_updates['is_disabled'] = is_disabled

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit submission language',
            sql=fr'UPDATE submission_language'
                fr'   SET {set_sql}'
                fr' WHERE id = %(language_id)s',
            language_id=language_id,
            **to_updates,
    ):
        pass


async def browse_language(include_disabled=True) -> Sequence[do.SubmissionLanguage]:
    async with SafeExecutor(
            event='Browse submission language',
            sql=fr'SELECT id, name, version, is_disabled'
                fr'  FROM submission_language'
                fr'{" WHERE NOT is_disabled" if not include_disabled else ""}'
                fr' ORDER BY name ASC, version ASC',
            fetch='all',
    ) as records:
        return [do.SubmissionLanguage(id=id_, name=name, version=version, is_disabled=is_disabled)
                for id_, name, version, is_disabled in records]


async def read_language(language_id: int, include_disabled=True) -> do.SubmissionLanguage:
    async with SafeExecutor(
            event='read submission language',
            sql=fr'SELECT id, name, version, is_disabled'
                fr'  FROM submission_language'
                fr' WHERE id = %(id)s'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}',
            id=language_id,
            fetch=1,
    ) as (id_, name, version, is_disabled):
        return do.SubmissionLanguage(id=id_, name=name, version=version, is_disabled=is_disabled)


# Submission


async def add(account_id: int, problem_id: int, language_id: int,
              content_file: str, content_length: str, submit_time: datetime) -> int:
    async with SafeExecutor(
            event='Add submission',
            sql="INSERT INTO submission"
                "            (account_id, problem_id, language_id,"
                "             content_file, content_length, submit_time)"
                "     VALUES (%(account_id)s, %(problem_id)s, %(language_id)s,"
                "             %(content_file)s, %(content_length)s, %(submit_time)s)"
                "  RETURNING id",
            account_id=account_id, problem_id=problem_id, language_id=language_id,
            content_file=content_file, content_length=content_length, submit_time=submit_time,
            fetch=1,
    ) as (id_,):
        return id_


# TODO: more filters
async def browse(account_id: int = None, problem_id: int = None, language_id: int = None) \
        -> Sequence[do.Submission]:
    conditions = {}

    if account_id is not None:
        conditions['account_id'] = account_id
    if problem_id is not None:
        conditions['problem_id'] = problem_id
    if language_id is not None:
        conditions['language_id'] = language_id

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='browse submissions',
            sql=fr'SELECT id, account_id, problem_id, language_id,'
                fr'       content_file, content_length, submit_time'
                fr'  FROM submission'
                fr' {f"WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id DESC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.Submission(id=id_, account_id=account_id, problem_id=problem_id,
                              language_id=language_id, content_file=content_file, content_length=content_length,
                              submit_time=submit_time)
                for id_, account_id, problem_id, language_id, content_file, content_length, submit_time
                in records]


async def read(submission_id: int) -> do.Submission:
    async with SafeExecutor(
            event='read submission',
            sql=fr'SELECT account_id, problem_id, language_id,'
                fr'       content_file, content_length, submit_time'
                fr'  FROM submission'
                fr' WHERE id = %(submission_id)s',
            submission_id=submission_id,
            fetch=1,
    ) as (account_id, problem_id, language_id, content_file, content_length, submit_time):
        return do.Submission(id=submission_id, account_id=account_id, problem_id=problem_id,
                             language_id=language_id, content_file=content_file, content_length=content_length,
                             submit_time=submit_time)
