from datetime import datetime
import typing
import uuid
from uuid import UUID

import persistence.database as db
import persistence.s3 as s3


async def add(file: typing.IO, filename: str, account_id: int, problem_id: int, language_id: int,
              submit_time: datetime) -> int:
    key = str(uuid.uuid4())
    bucket = await s3.submission.upload(file, key=key)

    content_file_uuid = await db.s3_file.add_with_uuid(uuid=UUID(key), bucket=bucket, key=key)

    submission_id = await db.submission.add(account_id=account_id, problem_id=problem_id,
                                            language_id=language_id,
                                            content_file_uuid=content_file_uuid,
                                            content_length=len(file.read()),
                                            filename=filename,
                                            submit_time=submit_time)

    return submission_id


edit = db.submission.edit
browse = db.submission.browse
read = db.submission.read

add_language = db.submission.add_language
edit_language = db.submission.edit_language
browse_language = db.submission.browse_language
read_language = db.submission.read_language
