from datetime import datetime
import typing

import persistence.database as db
import persistence.s3 as s3


async def add(file: typing.IO, filename: str, account_id: int, problem_id: int, language_id: int,
              submit_time: datetime) -> int:
    bucket, key = await s3.submission.upload(file)

    content_file_uuid = await db.s3_file.add(bucket=bucket, key=key, filename=filename)

    submission_id = await db.submission.add(account_id=account_id, problem_id=problem_id,
                                            language_id=language_id,
                                            content_file_uuid=content_file_uuid,
                                            content_length=len(file.read()),
                                            submit_time=submit_time)

    return submission_id


edit = db.submission.edit
browse = db.submission.browse
read = db.submission.read

add_language = db.submission.add_language
edit_language = db.submission.edit_language
browse_language = db.submission.browse_language
read_language = db.submission.read_language
