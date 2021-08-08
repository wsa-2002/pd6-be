from typing import Sequence, Tuple

from base import do

from .base import SafeExecutor


async def read_with_url(submission_id: int) -> Tuple[do.Submission, do.S3File]:
    async with SafeExecutor(
            event='read submission with url',
            sql=fr'SELECT submission.id, submission.account_id, submission.problem_id, submission.language_id,'
                fr'       submission.content_file_id, submission.content_length, submission.submit_time,'
                fr'       s3_file.id, s3_file.bucket, s3_file.key'
                fr'  FROM submission'
                fr' INNER JOIN s3_file'
                fr'    ON submission.content_file_id = s3_file.id'
                fr' WHERE submission.id = %(submission_id)s',
            submission_id=submission_id,
            fetch=1,
    ) as (id_, account_id, problem_id, language_id, content_file_id, content_length, submit_time,
          file_id, bucket, key):
        return (do.Submission(id=id_, account_id=account_id, problem_id=problem_id, language_id=language_id,
                              content_file_id=content_file_id, content_length=content_length, submit_time=submit_time),
                do.S3File(id=file_id, bucket=bucket, key=key))
