import typing
from typing import Optional
import uuid
from uuid import UUID

from base import do

from . import tools


_BUCKET_NAME = 'assisting-data'


async def upload(file: typing.IO, file_uuid: Optional[UUID] = None) -> do.S3File:
    return await tools.upload(bucket_name=_BUCKET_NAME, file=file, file_uuid=file_uuid or uuid.uuid4())
