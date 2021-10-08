import typing
from typing import Optional
import uuid
from uuid import UUID

from base import do

from . import s3_handler


_BUCKET_NAME = 'temp'


async def upload(file: typing.IO, file_uuid: Optional[UUID] = None) -> do.S3File:
    return await tools.upload(bucket_name=_BUCKET_NAME, file=file, file_uuid=file_uuid)


async def put_object(body, file_uuid: Optional[UUID] = None) -> do.S3File:
    """
    :return: infile content
    """
    if file_uuid is None:
        file_uuid = uuid.uuid4()

    key = str(file_uuid)
    await s3_handler.put_object(bucket=_BUCKET_NAME, key=key, body=body)
    return do.S3File(uuid=file_uuid, bucket=_BUCKET_NAME, key=key)