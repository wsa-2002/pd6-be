import typing
from typing import Optional
import uuid
from uuid import UUID

from base import do

from . import s3_handler, tools


_BUCKET_NAME = 'testdata'


async def upload(file: typing.IO, file_uuid: Optional[UUID] = None) -> do.S3File:
    return await tools.upload(bucket_name=_BUCKET_NAME, file=file, file_uuid=file_uuid)
