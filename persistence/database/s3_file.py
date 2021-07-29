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


async def read_by_key(key: str) -> do.S3File:
    async with SafeExecutor(
            event='read s3_file by key',
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
            sql=fr'INSERT INTO s3_file'
                fr'            (bucket, key)'
                fr'     VALUES (%(bucket)s, %(key)s)'
                fr'  RETURNING id',
            bucket=bucket, key=key,
            fetch=1,
    ) as (id_,):
        return id_


async def edit(s3_file_id: int,
               bucket: str = None,
               key: str = None) -> None:
    to_updates = {}

    if bucket is not None:
        to_updates['bucket'] = bucket
    if key is not None:
        to_updates['key'] = key

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit s3_file by id',
            sql=fr'UPDATE s3_file'
                fr'   SET {set_sql}'
                fr' WHERE id = %(s3_file_id)s',
            s3_file_id=s3_file_id,
            **to_updates,
    ):
        pass


async def delete(s3_file_id: int) -> None:
    async with SafeExecutor(
            event='delete s3_file',
            sql=fr'DELETE FROM s3_file'
                fr'      WHERE id = %(s3_file_id)s',
            s3_file_id=s3_file_id,
    ):
        pass
