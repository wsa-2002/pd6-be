import typing
from io import BytesIO

from fastapi import Header

from const import TESTDATA_ENCODING


def valid_file_length(file_length: int):
    async def validator(content_length: int = Header(..., lt=file_length)):
        return content_length
    return validator


def replace_cr(file: typing.IO) -> typing.IO:
    return BytesIO(file.read()
                   .decode(TESTDATA_ENCODING)
                   .replace('\r\n', '\n')
                   .encode(TESTDATA_ENCODING))
