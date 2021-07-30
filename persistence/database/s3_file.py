from typing import Sequence

from base import do
from .base import SafeExecutor


async def browse() -> Sequence[do.S3File]:
    async with SafeExecutor(
            event='browse s3_file',
            sql=fr'SELECT id, bucket, key'
                fr'  FROM s3_file'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.S3File(id=id_, bucket=bucket, key=key)
                for (id_, bucket, key)
                in records]


async def read(s3_file_id: int) -> do.S3File:
    async with SafeExecutor(
            event='read s3_file',
            sql=fr'SELECT id, bucket, key'
                fr'  FROM s3_file'
                fr' WHERE id = %(s3_file_id)s',
            s3_file_id=s3_file_id,
            fetch=1,
    ) as (id_, bucket, key):
        return do.S3File(id=id_, bucket=bucket, key=key)


async def add(bucket: str, key: str) -> int:
    async with SafeExecutor(
            event='add s3_file',
            sql=fr'INSERT INTO s3_file'
                fr'            (bucket, key)'
                fr'     VALUES (%(bucket)s, %(key)s)'
                fr'  RETURNING id',
            bucket=bucket, key=key,
            fetch=1,
    ) as (id_,):
        return id_
