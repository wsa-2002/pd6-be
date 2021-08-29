from datetime import datetime
from dataclasses import dataclass
import typing
from typing import Sequence
import uuid
from uuid import UUID

from base.popo import Filter, Sorter
from base import do, enum
import persistence.database as db
import persistence.s3 as s3


async def add(file: typing.IO, filename: str, account_id: int, problem_id: int, language_id: int,
              submit_time: datetime) -> int:
    file_uuid = uuid.uuid4()
    s3_file = await s3.submission.upload(file, file_uuid=file_uuid)

    content_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    submission_id = await db.submission.add(account_id=account_id, problem_id=problem_id,
                                            language_id=language_id,
                                            content_file_uuid=content_file_uuid,
                                            content_length=len(file.read()),
                                            filename=filename,
                                            submit_time=submit_time)

    return submission_id


edit = db.submission.edit
browse_under_class = db.submission.browse_under_class
read = db.submission.read

add_language = db.submission.add_language
edit_language = db.submission.edit_language
browse_language = db.submission.browse_language
read_language = db.submission.read_language
read_latest_judgment = db.submission.read_latest_judgment

get_problem_score_by_type = db.judgment.get_submission_judgment_by_challenge_type


@dataclass
class BrowseSubmissionOutput:
    id: int
    account_id: int
    problem_id: int
    language_id: int
    content_file_uuid: UUID
    content_length: int
    submit_time: datetime
    status: enum.JudgmentStatusType


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[BrowseSubmissionOutput], int]:
    submissions, total_count = await db.submission.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)

    result = []
    for submission in submissions:
        judgment = await db.submission.read_latest_judgment(submission_id=submission.id)
        result.append(BrowseSubmissionOutput(id=submission.id,
                                             account_id=submission.account_id,
                                             problem_id=submission.problem_id,
                                             language_id=submission.language_id,
                                             content_file_uuid=submission.content_file_uuid,
                                             content_length=submission.content_length,
                                             submit_time=submission.submit_time,
                                             status=judgment.status))

    return result, total_count
