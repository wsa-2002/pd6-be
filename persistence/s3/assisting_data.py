import typing
from uuid import UUID

from base import do

from . import s3_handler


_BUCKET_NAME = 'assisting-data'


async def upload(file: typing.IO, key: str) -> do.S3File:
    """
    :return: bucket name
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    await bucket.upload_fileobj(file, key)
    return do.S3File(uuid=UUID(key), bucket=_BUCKET_NAME, key=key)
