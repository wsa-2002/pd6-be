from datetime import datetime
from typing import Sequence
from uuid import UUID

from base import do

from .base import SafeExecutor


async def browse(account_id: int = None, essay_id: int = None) -> Sequence[do.EssaySubmission]:
    conditions = {}
    if account_id is not None:
        conditions['account_id'] = account_id
    if essay_id is not None:
        conditions['essay_id'] = essay_id

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='browse essay_submission',
            sql=fr'SELECT id, account_id, essay_id, content_file_uuid, filename, submit_time'
                fr'  FROM essay_submission'
                fr' {f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id DESC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.EssaySubmission(id=id_, account_id=account_id, essay_id=essay_id,
                                   content_file_uuid=content_file_uuid, filename=filename, submit_time=submit_time)
                for (id_, account_id, essay_id, content_file_uuid, filename, submit_time) in records]


async def read(essay_submission_id: int) -> do.EssaySubmission:
    async with SafeExecutor(
            event='read essay_submission',
            sql=fr'SELECT id, account_id, essay_id, content_file_uuid, filename, submit_time'
                fr'  FROM essay_submission'
                fr' WHERE id = %(essay_submission_id)s',
            essay_submission_id=essay_submission_id,
            fetch=1,
    ) as (id_, account_id, essay_id, content_file_uuid, filename, submit_time):
        return do.EssaySubmission(id=id_, account_id=account_id, essay_id=essay_id,
                                  content_file_uuid=content_file_uuid, filename=filename, submit_time=submit_time)


async def add(account_id: int, essay_id: int, content_file_uuid: UUID, filename: str, submit_time: datetime) -> int:
    async with SafeExecutor(
            event='add essay-submission',
            sql=fr"INSERT INTO essay_submission"
                fr"            (account_id, essay_id, content_file_uuid, filename, submit_time)"
                fr"     VALUES (%(account_id)s, %(essay_id)s, %(content_file_uuid)s, %(filename)s, %(submit_time)s)"
                fr"  RETURNING id",
            account_id=account_id, essay_id=essay_id, content_file_uuid=content_file_uuid,
            filename=filename, submit_time=submit_time,
            fetch=1,
    ) as (essay_submission_id, ):
        return essay_submission_id


async def edit(essay_submission_id: int, content_file_uuid: UUID, filename: str, submit_time: datetime) -> None:
    async with SafeExecutor(
            event='update essay_submission by id',
            sql=fr"UPDATE essay_submission"
                fr"   SET content_file_uuid = %(content_file_uuid)s, filename = %(filename)s,"
                  "                           submit_time = %(submit_time)s"
                fr" WHERE id = %(essay_submission_id)s",
            content_file_uuid=content_file_uuid, filename=filename, submit_time=submit_time,
            essay_submission_id=essay_submission_id,
    ):
        pass
