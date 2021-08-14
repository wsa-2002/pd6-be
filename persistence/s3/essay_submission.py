import typing

from . import s3_handler


_BUCKET_NAME = 'essay-submission'


async def upload(file: typing.IO, key: str) -> str:
    """
    :return: bucket name
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    await bucket.upload_fileobj(file, key)
    return _BUCKET_NAME
