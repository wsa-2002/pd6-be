from dataclasses import dataclass
from fastapi import File, UploadFile

import util
import persistence.database as db
from . import s3_handler
import aioboto3
import log
from config import S3Config as s3_config


@dataclass
class S3UploadOutput:
    bucket: str
    key: str


async def upload_input(testcase_id: int, file: UploadFile) -> S3UploadOutput:
    session = aioboto3.Session()
    bucket = 'testcase'
    key = f'{testcase_id}/input-data/{util.get_request_uuid()}/{file.filename}'
    async with session.client(
                's3',
                endpoint_url=f'https://{s3_config.host}:{s3_config.port}',
                aws_access_key_id=s3_config.access_key,
                aws_secret_access_key=s3_config.secret_key
            ) as s3:
        await s3.upload_fileobj(file.file, bucket, key)
    return S3UploadOutput(bucket=bucket, key=key)


async def upload_output(testcase_id: int, file: UploadFile) -> S3UploadOutput:
    session = aioboto3.Session()
    bucket = 'testcase'
    key = f'{testcase_id}/output-data/{util.get_request_uuid()}/{file.filename}'
    async with session.client(
                's3',
                endpoint_url=f'https://{s3_config.host}:{s3_config.port}',
                aws_access_key_id=s3_config.access_key,
                aws_secret_access_key=s3_config.secret_key
            ) as s3:
        await s3.upload_fileobj(file.file, bucket, key)
    return S3UploadOutput(bucket=bucket, key=key)


async def delete(file_id: int) -> None:
    s3_file = await db.s3_file.read_by_id(file_id=file_id)
    session = aioboto3.Session()
    async with session.client(
            's3',
            endpoint_url=f'https://{s3_config.host}:{s3_config.port}',
            aws_access_key_id=s3_config.access_key,
            aws_secret_access_key=s3_config.secret_key
    ) as s3:
        await s3.delete_object(Bucket=s3_file.bucket, Key=s3_file.key)


async def download(key: str) -> None:
    filename = key[key.rfind('/') + 1:]
    s3_file = await db.s3_file.read_by_key(key=key)
    session = aioboto3.Session()
    async with session.client(
            's3',
            endpoint_url=f'https://{s3_config.host}:{s3_config.port}',
            aws_access_key_id=s3_config.access_key,
            aws_secret_access_key=s3_config.secret_key
    ) as s3:
        await s3.download_file(s3_file.bucket, key, filename)