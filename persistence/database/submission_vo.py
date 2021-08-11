from typing import Sequence, Tuple

from base import do

from .base import SafeExecutor


async def browse_with_url(account_id: int = None, problem_id: int = None, language_id: int = None) -> Sequence[
    Tuple[do.Submission, do.S3File]]:
    conditions = {}

    if account_id is not None:
        conditions['account_id'] = account_id
    if problem_id is not None:
        conditions['problem_id'] = problem_id
    if language_id is not None:
        conditions['language_id'] = language_id

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='browse submission with url',
            sql=fr'SELECT submission.id, submission.account_id, submission.problem_id, submission.language_id,'
                fr'       submission.content_file_uuid, submission.content_length, submission.submit_time,'
                fr'       s3_file.uuid, s3_file.bucket, s3_file.key, s3_file.filename'
                fr'  FROM submission'
                fr' INNER JOIN s3_file'
                fr'    ON submission.content_file_uuid = s3_file.uuid'
                fr' {f"WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id DESC',
            **conditions,
            fetch='all',
    ) as records:
        return [(do.Submission(id=id_, account_id=account_id, problem_id=problem_id,
                               language_id=language_id, content_file_uuid=content_file_uuid, content_length=content_length,
                               submit_time=submit_time),
                 do.S3File(uuid=file_uuid, bucket=bucket, key=key, filename=filename))
                for (id_, account_id, problem_id, language_id, content_file_uuid, content_length, submit_time,
                     file_uuid, bucket, key) in records]


async def read_with_url(submission_id: int) -> Tuple[do.Submission, do.S3File]:
    async with SafeExecutor(
            event='read submission with url',
            sql=fr'SELECT submission.id, submission.account_id, submission.problem_id, submission.language_id,'
                fr'       submission.content_file_uuid, submission.content_length, submission.submit_time,'
                fr'       s3_file.uuid, s3_file.bucket, s3_file.key, s3_file.filename'
                fr'  FROM submission'
                fr' INNER JOIN s3_file'
                fr'    ON submission.content_file_uuid = s3_file.uuid'
                fr' WHERE submission.id = %(submission_id)s',
            submission_id=submission_id,
            fetch=1,
    ) as (id_, account_id, problem_id, language_id, content_file_uuid, content_length, submit_time,
          file_uuid, bucket, key):
        return (do.Submission(id=id_, account_id=account_id, problem_id=problem_id, language_id=language_id,
                              content_file_uuid=content_file_uuid, content_length=content_length, submit_time=submit_time),
                do.S3File(uuid=file_uuid, bucket=bucket, key=key, filename=filename))
