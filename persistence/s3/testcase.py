from dataclasses import dataclass
from fastapi import UploadFile

import util
import persistence.database as db
from . import s3_handler


@dataclass
class S3UploadOutput:
    bucket: str
    key: str


async def upload_input(testcase_id: int, file: UploadFile) -> S3UploadOutput:
    bucket = 'testcase'
    key = f'{testcase_id}/input-data/{util.get_request_uuid()}/{file.filename}'
    async with s3_handler.client as client:
        await client.upload_fileobj(file, bucket, key)
        return S3UploadOutput(bucket=bucket, key=key)


async def upload_output(testcase_id: int, file: UploadFile) -> S3UploadOutput:
    bucket = 'testcase'
    key = f'{testcase_id}/output-data/{util.get_request_uuid()}/{file.filename}'
    async with s3_handler.client as client:
        await client.upload_fileobj(file, bucket, key)
        return S3UploadOutput(bucket=bucket, key=key)


async def delete(testcase_id: int) -> None:
    s3_file = await db.s3_file.read_by_id(file_id=testcase_id)
    async with s3_handler.client as client:
        await client.delete_object(Bucket=s3_file.bucket, Key=s3_file.key)


async def download(key: str) -> None:
    filename = key[key.rfind('/') + 1:]
    s3_file = await db.s3_file.read_by_key(key=key)
    async with s3_handler.client as client:
        await client.download_file(s3_file.bucket, key, filename)