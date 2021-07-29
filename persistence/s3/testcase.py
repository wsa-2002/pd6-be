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


async def update(file: typing.IO, key: str) -> Tuple[str, str]:
    """
    :return: bucket name and key
    """
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    await bucket.upload_fileobj(file, key)
    return _BUCKET_NAME, key


async def delete(bucket: str, key: str) -> None:
    to_delete_file = await s3_handler.resource.Object(bucket, key)
    await to_delete_file.delete()


async def download(key: str, filename: str) -> None:
    bucket = await s3_handler.get_bucket(_BUCKET_NAME)
    await bucket.download_file(key, filename)
