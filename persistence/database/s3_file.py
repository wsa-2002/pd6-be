from typing import Sequence
from uuid import UUID

from base import do

from .base import SafeExecutor


async def browse() -> Sequence[do.S3File]:
    async with SafeExecutor(
            event='browse s3_file',
            sql=fr'SELECT uuid, bucket, key, filename'
                fr'  FROM s3_file'
                fr' ORDER BY uuid ASC',
            fetch='all',
    ) as records:
        return [do.S3File(uuid=uuid, bucket=bucket, key=key, filename=filename)
                for (uuid, bucket, key)
                in records]


async def read(s3_file_uuid: UUID) -> do.S3File:
    async with SafeExecutor(
            event='read s3_file',
            sql=fr'SELECT uuid, bucket, key, filename'
                fr'  FROM s3_file'
                fr' WHERE uuid = %(s3_file_uuid)s',
            s3_file_uuid=s3_file_uuid,
            fetch=1,
    ) as (uuid, bucket, key):
        return do.S3File(uuid=uuid, bucket=bucket, key=key, filename=filename)


async def add(bucket: str, key: str, filename: str) -> UUID:
    async with SafeExecutor(
            event='add s3_file',
            sql=fr'INSERT INTO s3_file'
                fr'            (bucket, key, filename)'
                fr'     VALUES (%(bucket)s, %(key)s, %(filename)s)'
                fr'  RETURNING uuid',
            bucket=bucket, key=key, filename=filename,
            fetch=1,
    ) as (uuid,):
        return uuid
