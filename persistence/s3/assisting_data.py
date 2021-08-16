import io
import typing
from typing import Optional
import uuid
from uuid import UUID

from base import do

from . import s3_handler


_BUCKET_NAME = 'assisting-data'


async def upload(file: typing.IO, file_uuid: Optional[UUID] = None) -> do.S3File:
    """
    :return: do.S3File
    """
    if file_uuid is None:
        file_uuid = uuid.uuid4()

    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    key = str(file_uuid)
    await bucket.upload_fileobj(file, key)
    return do.S3File(uuid=file_uuid, bucket=_BUCKET_NAME, key=key)


async def download(key: str) -> typing.IO:
    """
    :return: file-like object: typing.IO
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)

    with io.BytesIO() as file:
        return await bucket.download_fileobj(key, file)
