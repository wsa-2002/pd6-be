from datetime import datetime
from typing import Optional, Sequence

from base import do

from .base import SafeExecutor


# Submission Language


async def add_language(name: str, version: str) -> int:
    async with SafeExecutor(
            event='Add submission language',
            sql="INSERT INTO submission_language"
                "            (name, version)"
                "     VALUES (%(name)s, %(version)s)"
                "  RETURNING id",
            name=name, version=version,
            fetch=1,
    ) as (id_,):
        return id_


async def browse_language() -> Sequence[do.SubmissionLanguage]:
    async with SafeExecutor(
            event='Browse submission language',
            sql="SELECT id, name, version"
                "  FROM submission_language"
                " ORDER BY name ASC, version ASC",
            fetch='all',
    ) as records:
        return [do.SubmissionLanguage(id=id_, name=name, version=version)
                for id_, name, version in records]


async def read_language(language_id: int) -> do.SubmissionLanguage:
    async with SafeExecutor(
            event='read submission language',
            sql="SELECT name, version"
                "  FROM submission_language"
                " WHERE id = %(id)s",
            id=language_id,
            fetch=1,
    ) as (name, version):
        return do.SubmissionLanguage(id=language_id, name=name, version=version)


async def delete_language(language_id: int) -> None:
    ...  # TODO (應該是 soft-delete)


# Submission


async def add(account_id: int, problem_id: int, challenge_id: Optional[int], language_id: int,
              content_file: str, content_length: str, submit_time: datetime) -> int:
    async with SafeExecutor(
            event='Add submission',
            sql="INSERT INTO submission"
                "            (account_id, problem_id, challenge_id, language_id,"
                "             content_file, content_length, submit_time)"
                "     VALUES (%(account_id)s, %(problem_id)s, %(challenge_id)s, %(language_id)s,"
                "             %(content_file)s, %(content_length)s, %(submit_time)s)"
                "  RETURNING id",
            account_id=account_id, problem_id=problem_id, challenge_id=challenge_id, language_id=language_id,
            content_file=content_file, content_length=content_length, submit_time=submit_time,
            fetch=1,
    ) as (id_,):
        return id_


# TODO: more filters
async def browse(account_id: int = None, problem_id: int = None, challenge_id: int = None, language_id: int = None) \
        -> Sequence[do.Submission]:
    conditions = {}

    if account_id is not None:
        conditions['account_id'] = account_id
    if problem_id is not None:
        conditions['problem_id'] = problem_id
    if challenge_id is not None:
        conditions['challenge_id'] = challenge_id
    if language_id is not None:
        conditions['language_id'] = language_id

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='browse submissions',
            sql=fr'SELECT id, account_id, problem_id, challenge_id, language_id,'
                fr'       content_file, content_length, submit_time'
                fr'  FROM submission'
                fr' {f"WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id DESC',
            fetch='all',
    ) as records:
        return [do.Submission(id=id_, account_id=account_id, problem_id=problem_id, challenge_id=challenge_id,
                              language_id=language_id, content_file=content_file, content_length=content_length,
                              submit_time=submit_time)
                for id_, account_id, problem_id, challenge_id, language_id, content_file, content_length, submit_time
                in records]


async def read(submission_id: int) -> do.Submission:
    async with SafeExecutor(
            event='read submission',
            sql=fr'SELECT account_id, problem_id, challenge_id, language_id,'
                fr'       content_file, content_length, submit_time'
                fr'  FROM submission'
                fr' WHERE id = %(submission_id)s',
            submission_id=submission_id,
            fetch=1,
    ) as (account_id, problem_id, challenge_id, language_id, content_file, content_length, submit_time):
        return do.Submission(id=submission_id, account_id=account_id, problem_id=problem_id, challenge_id=challenge_id,
                             language_id=language_id, content_file=content_file, content_length=content_length,
                             submit_time=submit_time)
