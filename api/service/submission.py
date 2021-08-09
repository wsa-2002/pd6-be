from datetime import datetime
import typing

import persistence.database as db
import persistence.s3 as s3


browse_with_url = db.submission_vo.browse_with_url
read_with_url = db.submission_vo.read_with_url


async def add(file: typing.IO, filename: str, account_id: int, problem_id: int, language_id: int,
              submit_time: datetime) -> int:
    bucket, key = await s3.submission.upload(file=file, filename=filename)

    content_file_id = await db.s3_file.add(bucket=bucket, key=key)

    submission_id = await db.submission.add(account_id=account_id, problem_id=problem_id,
                                            language_id=language_id,
                                            content_file_id=content_file_id,
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
