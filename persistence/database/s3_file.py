from typing import Sequence

import log
from base import do

from .base import SafeExecutor


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


async def read_by_key(key: str) -> do.S3File:
    async with SafeExecutor(
            event='read s3_file',
            sql=fr'SELECT id, bucket, key'
                fr'  FROM s3_file'
                fr' WHERE key = %(key)s',
            key=key,
            fetch=1,
    ) as (id_, bucket, key):
        return do.S3File(id=id_, bucket=bucket, key=key)


async def add(bucket: str, key: str) -> int:
    async with SafeExecutor(
            event='add s3_file',
            sql=r'INSERT INTO s3_file'
                r'            (bucket, key)'
                r'     VALUES (%(bucket)s, %(key)s)'
                r'  RETURNING id',
            bucket=bucket, key=key,
            fetch=1,
    ) as (id_,):
        return id_


async def delete(s3_file_id: int) -> None:
    async with SafeExecutor(
            event='delete s3_file',
            sql=fr'DELETE FROM s3_file'
                fr'      WHERE id = %(s3_file_id)s',
            s3_file_id=s3_file_id,
    ):
        pass
