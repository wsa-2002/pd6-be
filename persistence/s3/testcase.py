from fastapi import UploadFile

import util
from . import s3_handler


async def upload_input(testcase_id: int, file: UploadFile) -> None:
    key = f'{testcase_id}/input-data/{util.get_request_uuid()}/{file.filename}'
    async with s3_handler.resource as res:
        bucket = await res.Bucket('testcase')
        await bucket.upload_fileobj(file.file, key)