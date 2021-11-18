import typing
from io import BytesIO

from fastapi import Header

import const
import exceptions as exc


def valid_file_length(file_length: int):
    async def validator(content_length: int = Header(..., lt=file_length)):
        return content_length
    return validator


def replace_cr(file: typing.IO) -> typing.IO:
    try:
        return BytesIO(file.read()
                       .decode(const.TESTDATA_ENCODING)
                       .replace('\r\n', '\n')
                       .encode(const.TESTDATA_ENCODING))
    except UnicodeDecodeError:
        raise exc.FileDecodeError
