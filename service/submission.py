from datetime import datetime
import typing
import uuid

import persistence.database as db
import persistence.s3 as s3


async def add(file: typing.IO, filename: str, account_id: int, problem_id: int, language_id: int,
              file_length: int, submit_time: datetime) -> int:
    file_uuid = uuid.uuid4()
    s3_file = await s3.submission.upload(file, file_uuid=file_uuid)

    content_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    submission_id = await db.submission.add(account_id=account_id, problem_id=problem_id,
                                            language_id=language_id,
                                            content_file_uuid=content_file_uuid,
                                            content_length=file_length, filename=filename,
                                            submit_time=submit_time)

    return submission_id


browse = db.submission.browse
browse_with_submission_ids = db.judgment.browse_latest_with_submission_ids
edit = db.submission.edit
browse_under_class = db.submission.browse_under_class
read = db.submission.read

add_language = db.submission.add_language
edit_language = db.submission.edit_language
browse_language = db.submission.browse_language
read_language = db.submission.read_language
read_latest_judgment = db.submission.read_latest_judgment

get_problem_score_by_type = db.judgment.read_by_challenge_type
get_problem_all_time_best_score = db.judgment.get_best_submission_judgment_all_time
