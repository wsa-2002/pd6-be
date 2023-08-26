from typing import Sequence, Iterable, Optional
from uuid import UUID

from base import do

from .base import AutoTxConnection, FetchOne, FetchAll


async def browse() -> Sequence[do.S3File]:
    async with FetchAll(
            event='browse s3_file',
            sql=r'SELECT uuid, bucket, key'
                r'  FROM s3_file'
                r' ORDER BY uuid ASC',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.S3File(uuid=uuid, bucket=bucket, key=key)
                for (uuid, bucket, key)
                in records]


async def browse_with_uuids(uuids: Iterable[UUID]) -> Sequence[Optional[do.S3File]]:
    value_sql = ','.join(f'(\'{uuid}\')' for uuid in uuids)
    if not value_sql:
        return []

    async with AutoTxConnection(event='browse s3 file with uuids') as conn:
        return [do.S3File(uuid=uuid, bucket=bucket, key=key)
                if uuid else None
                for (uuid, bucket, key)
                in await conn.fetch(fr'SELECT s3_file.uuid, s3_file.bucket, s3_file.key'
                                    fr'  FROM (VALUES {value_sql}) given_uuids(given_uuid)'
                                    fr'  LEFT JOIN s3_file'
                                    fr'         ON s3_file.uuid = given_uuids.given_uuid::UUID')]


async def read(s3_file_uuid: UUID) -> do.S3File:
    async with FetchOne(
            event='read s3_file',
            sql=r'SELECT uuid, bucket, key'
                r'  FROM s3_file'
                r' WHERE uuid = %(s3_file_uuid)s',
            s3_file_uuid=s3_file_uuid,
    ) as (uuid, bucket, key):
        return do.S3File(uuid=uuid, bucket=bucket, key=key)


async def add(bucket: str, key: str) -> UUID:
    async with FetchOne(
            event='add s3_file',
            sql=r'INSERT INTO s3_file'
                r'            (bucket, key)'
                r'     VALUES (%(bucket)s, %(key)s)'
                r'  RETURNING uuid',
            bucket=bucket, key=key,
    ) as (uuid,):
        return uuid


async def add_with_do(s3_file: do.S3File) -> UUID:
    async with FetchOne(
            event='add s3_file with uuid',
            sql=r'INSERT INTO s3_file'
                r'            (uuid, bucket, key)'
                r'     VALUES (%(uuid)s, %(bucket)s, %(key)s)'
                r'  RETURNING uuid',
            uuid=s3_file.uuid, bucket=s3_file.bucket, key=s3_file.key,
    ) as (uuid,):
        return uuid
