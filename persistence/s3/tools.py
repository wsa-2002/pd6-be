import io
import typing
from typing import Optional
import uuid
from uuid import UUID

import log
from base import do

from . import s3_handler


async def sign_url(bucket: str, key: str, expire_secs: int, filename: str, as_attachment: bool) -> str:
    return await s3_handler.sign_url(
        bucket=bucket,
        key=key,
        as_filename=filename,
        expire_secs=expire_secs,
        as_attachment=as_attachment,
    )


async def sign_url_from_do(s3_file: do.S3File, expire_secs: int, filename: str, as_attachment: bool) -> str:
    return await sign_url(
        bucket=s3_file.bucket,
        key=s3_file.key,
        filename=filename,
        expire_secs=expire_secs,
        as_attachment=as_attachment,
    )


async def get_file_content(bucket: str, key: str):
    """
    :return: infile content
    """
    return await s3_handler.get_file_content(bucket=bucket, key=key)


async def upload(bucket_name: str, file: typing.IO, file_uuid: Optional[UUID] = None) -> do.S3File:
    """
    :return: do.S3File
    """
    if file_uuid is None:
        file_uuid = uuid.uuid4()

    bucket = await s3_handler.get_bucket(bucket_name)
    key = str(file_uuid)
    await bucket.upload_fileobj(file, key)
    log.info(f'S3 file uploaded: {bucket_name=}, {file_uuid=}')
    return do.S3File(uuid=file_uuid, bucket=bucket_name, key=key)
