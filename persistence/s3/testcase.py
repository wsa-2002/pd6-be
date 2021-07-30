import typing
from typing import Tuple
import uuid

from . import s3_handler

_BUCKET_NAME = 'testcase'


async def upload_input(file: typing.IO, filename: str, testcase_id: int) -> Tuple[str, str]:
    """
    :return: bucket name and key
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    key = f'{testcase_id}/input-data/{uuid.uuid4()}/{filename}'
    await bucket.upload_fileobj(file, key)
    return _BUCKET_NAME, key


async def upload_output(file: typing.IO, filename: str, testcase_id: int) -> Tuple[str, str]:
    """
    :return: bucket name and key
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    key = f'{testcase_id}/output-data/{uuid.uuid4()}/{filename}'
    await bucket.upload_fileobj(file, key)
    return _BUCKET_NAME, key
