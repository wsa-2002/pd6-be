from datetime import datetime
from typing import Sequence
from uuid import UUID

from base import do
from base.popo import Filter, Sorter

from .base import FetchOne, FetchAll, OnlyExecute
from .util import execute_count, compile_filters


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[do.EssaySubmission], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse essay_submission',
            sql=fr'SELECT id, account_id, essay_id, content_file_uuid, filename, submit_time'
                fr'  FROM essay_submission'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} id DESC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.EssaySubmission(id=id_, account_id=account_id, essay_id=essay_id,
                                   content_file_uuid=content_file_uuid, filename=filename, submit_time=submit_time)
                for (id_, account_id, essay_id, content_file_uuid, filename, submit_time) in records]

    total_count = await execute_count(
        sql=fr'SELECT id, account_id, essay_id, content_file_uuid, filename, submit_time'
            fr'  FROM essay_submission'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def browse_with_essay_id(essay_id: int, include_deleted=False) \
        -> Sequence[do.EssaySubmission]:
    async with FetchAll(
            event='browse testcases with problem id',
            sql=fr'SELECT essay_submission.id, essay_submission.account_id, essay_submission.essay_id,' 
                fr'       essay_submission.content_file_uuid, essay_submission.filename, essay_submission.submit_time'
                fr'  FROM essay_submission'
                fr' INNER JOIN essay'
                fr'         ON essay.id = essay_submission.essay_id'
                fr'      WHERE essay_submission.essay_id = %(essay_id)s'
                fr'{"  AND NOT essay.is_deleted" if not include_deleted else ""}',
            essay_id=essay_id,
    ) as records:
        return [do.EssaySubmission(id=id_, account_id=account_id, essay_id=essay_id,
                                   content_file_uuid=content_file_uuid, filename=filename, submit_time=submit_time)
                for (id_, account_id, essay_id, content_file_uuid, filename, submit_time)
                in records]


async def read(essay_submission_id: int) -> do.EssaySubmission:
    async with FetchOne(
            event='read essay_submission',
            sql=fr'SELECT id, account_id, essay_id, content_file_uuid, filename, submit_time'
                fr'  FROM essay_submission'
                fr' WHERE id = %(essay_submission_id)s',
            essay_submission_id=essay_submission_id,
    ) as (id_, account_id, essay_id, content_file_uuid, filename, submit_time):
        return do.EssaySubmission(id=id_, account_id=account_id, essay_id=essay_id,
                                  content_file_uuid=content_file_uuid, filename=filename, submit_time=submit_time)


async def add(account_id: int, essay_id: int, content_file_uuid: UUID, filename: str, submit_time: datetime) -> int:
    async with FetchOne(
            event='add essay-submission',
            sql=fr"INSERT INTO essay_submission"
                fr"            (account_id, essay_id, content_file_uuid, filename, submit_time)"
                fr"     VALUES (%(account_id)s, %(essay_id)s, %(content_file_uuid)s, %(filename)s, %(submit_time)s)"
                fr"  RETURNING id",
            account_id=account_id, essay_id=essay_id, content_file_uuid=content_file_uuid,
            filename=filename, submit_time=submit_time,
    ) as (essay_submission_id, ):
        return essay_submission_id


async def edit(essay_submission_id: int, content_file_uuid: UUID, filename: str, submit_time: datetime) -> None:
    async with OnlyExecute(
            event='update essay_submission by id',
            sql=fr"UPDATE essay_submission"
                fr"   SET content_file_uuid = %(content_file_uuid)s, filename = %(filename)s,"
                  "                           submit_time = %(submit_time)s"
                fr" WHERE id = %(essay_submission_id)s",
            content_file_uuid=content_file_uuid, filename=filename, submit_time=submit_time,
            essay_submission_id=essay_submission_id,
    ):
        pass


async def browse_by_essay_class_members(essay_id: int) -> dict[int, do.EssaySubmission]:
    """
    Only supports last
    Returns only submitted members

    :return: member_id, essay_submission
    """

    async with FetchAll(
            event='browse essay submission by essay class members',
            sql=fr'SELECT DISTINCT ON (class_member.member_id)'
                fr'       class_member.member_id,'
                fr'       essay_submission.id, essay_submission.account_id, essay_submission.essay_id,'
                fr'       essay_submission.content_file_uuid, essay_submission.filename, essay_submission.submit_time'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON challenge.class_id = class_member.class_id'
                fr'        AND NOT challenge.is_deleted'
                fr' INNER JOIN essay'
                fr'         ON essay.challenge_id = challenge.id'
                fr'        AND NOT essay.is_deleted'
                fr'        AND essay.id = %(essay_id)s'
                fr' INNER JOIN essay_submission'
                fr'         ON essay_submission.essay_id = essay.id'
                fr'        AND essay_submission.account_id = class_member.member_id'
                fr'        AND essay_submission.submit_time <= challenge.end_time'
                fr' ORDER BY class_member.member_id, essay_submission.submit_time DESC, essay_submission.id DESC',
            essay_id=essay_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return {member_id: do.EssaySubmission(id=essay_submission_id, account_id=account_id, essay_id=essay_id,
                                              content_file_uuid=content_file_uuid, filename=filename,
                                              submit_time=submit_time)
                for member_id, essay_submission_id, account_id, essay_id, content_file_uuid, filename, submit_time
                in records}
