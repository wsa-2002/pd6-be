import typing
from typing import Tuple
import uuid

from . import s3_handler

_BUCKET_NAME = 'testdata'


async def upload(file: typing.IO) -> Tuple[str, str]:
    """
    :return: bucket name and key
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    key = str(uuid.uuid4())
    await bucket.upload_fileobj(file, key)
    return _BUCKET_NAME, key
