import typing
from typing import Tuple
import uuid

from . import s3_handler


_BUCKET_NAME = 'essay_submission'


async def upload(file: typing.IO, filename: str) -> Tuple[str, str]:
    """
    :return: bucket name and key
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    key = f'{uuid.uuid4()}/{filename}'
    await bucket.upload_fileobj(file, key)
    return _BUCKET_NAME, key
