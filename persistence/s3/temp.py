from datetime import datetime
import typing
from typing import Optional
import uuid
from uuid import UUID

from base import do
import log

from . import s3_handler, tools


_BUCKET_NAME = 'temp'


async def upload(file: typing.IO, file_uuid: Optional[UUID] = None) -> do.S3File:
    return await tools.upload(bucket_name=_BUCKET_NAME, file=file, file_uuid=file_uuid or uuid.uuid4())


async def put_object(body, file_uuid: Optional[UUID] = None) -> do.S3File:
    """
    :return: infile content
    """
    start_time = datetime.now()
    log.info('Start putting S3 files ...')

    if file_uuid is None:
        file_uuid = uuid.uuid4()

    key = str(file_uuid)
    await s3_handler.put_object(bucket=_BUCKET_NAME, key=key, body=body)

    exec_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    log.info(f'Ended put S3 file after {exec_time_ms} ms')

    return do.S3File(uuid=file_uuid, bucket=_BUCKET_NAME, key=key)
