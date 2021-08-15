from datetime import datetime
import typing
import uuid

import persistence.database as db
import persistence.s3 as s3


read = db.essay_submission.read
browse = db.essay_submission.browse


async def add(file: typing.IO, filename: str, account_id: int, essay_id: int, submit_time: datetime) -> int:
    file_uuid = uuid.uuid4()
    s3_file = await s3.essay_submission.upload(file, file_uuid=file_uuid)

    content_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    essay_submission_id = await db.essay_submission.add(account_id=account_id, essay_id=essay_id,
                                                        content_file_uuid=content_file_uuid, filename=filename,
                                                        submit_time=submit_time)

    return essay_submission_id


async def edit(file: typing.IO, filename: str, essay_submission_id: int, submit_time: datetime):
    file_uuid = uuid.uuid4()
    s3_file = await s3.essay_submission.upload(file, file_uuid=file_uuid)

    content_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    await db.essay_submission.edit(essay_submission_id=essay_submission_id,
                                   content_file_uuid=content_file_uuid, filename=filename,
                                   submit_time=submit_time)
