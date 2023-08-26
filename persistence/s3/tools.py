import io
import zipfile
import typing
from uuid import UUID
from datetime import datetime

import const
import log
from base import do

from . import s3_handler


async def sign_url(bucket: str, key: str, filename: str, as_attachment: bool, expire_secs: int = const.S3_EXPIRE_SECS) \
        -> str:
    start_time = datetime.now()
    log.info('Start getting S3 file sign url ...')

    sign_url = await s3_handler.sign_url(
        bucket=bucket,
        key=key,
        as_filename=filename,
        expire_secs=expire_secs,
        as_attachment=as_attachment,
    )

    exec_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    log.info(f'Ended get S3 file {sign_url=} after {exec_time_ms} ms')

    return sign_url


async def sign_url_from_do(s3_file: do.S3File, expire_secs: int, filename: str, as_attachment: bool) -> str:
    return await sign_url(
        bucket=s3_file.bucket,
        key=s3_file.key,
        filename=filename,
        expire_secs=expire_secs,
        as_attachment=as_attachment,
    )


async def get_file_content(bucket: str, key: str) -> bytes:
    """
    :return: infile content
    """
    log.info('Getting S3 file content...')
    return await s3_handler.get_file_content(bucket=bucket, key=key)


async def get_file_content_from_do(s3_file: do.S3File) -> bytes:
    """
    :return: infile content
    """
    return await s3_handler.get_file_content(bucket=s3_file.bucket, key=s3_file.key)


async def upload(bucket_name: str, file: typing.IO, file_uuid: UUID) -> do.S3File:
    """
    :return: do.S3File
    """
    start_time = datetime.now()
    log.info(f'Starting S3 file upload: {bucket_name=}, {file_uuid=}')

    bucket = await s3_handler.get_bucket(bucket_name)
    key = str(file_uuid)
    await bucket.upload_fileobj(file, key)

    exec_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    log.info(f'Ended S3 file upload after {exec_time_ms} ms')

    return do.S3File(uuid=file_uuid, bucket=bucket_name, key=key)


async def zipper(files: dict[str, do.S3File]) -> io.BytesIO:
    start_time = datetime.now()
    log.info('Start zipping S3 files ...')

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for filename, file in files.items():
            infile_content = await get_file_content(bucket=file.bucket, key=file.key)
            zip_file.writestr(filename, infile_content)

    exec_time_ms = (datetime.now() - start_time).total_seconds() * 1000
    log.info(f'Ended zip S3 file after {exec_time_ms} ms')

    return zip_buffer
