import datetime
import json
import typing

from pydantic import BaseModel, create_model

import exceptions as exc

import fastapi.exceptions
import fastapi.routing

import exceptions
import log


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return super().default(obj)


class JSONResponse(fastapi.routing.JSONResponse):
    def __init__(self, *args, success=True, error: Exception = None, **kwargs):
        self._success = success
        self._error = error
        super().__init__(*args, **kwargs)

        def render(self, content: typing.Any) -> bytes:
        return json.dumps({
            'success': self._success,
            'data': content,
            'error': self._error.__class__.__name__ if self._error else None,
        }, cls=JSONEncoder,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


def pack_response_model(Model: typing.Type[BaseModel], name: str):
    if Model in (None, type(None)):
        # data is None -> no data
        return create_model(
            name,
            success=(bool, ...),
            error=(typing.Any, None),
        )

    return create_model(  # Normal case
        name,
        success=(bool, ...),
        data=(Model, ...),
        error=(typing.Any, None),
    )


async def exception_handler(request, error: Exception):
    # Convert Pydantic's ValidationError to self-defined error
    if isinstance(error, fastapi.exceptions.ValidationError):
        error = exc.IllegalInput(cause=error)

    is_predefined = isinstance(error, exceptions.PdogsException)
    log.exception(error, info_level=is_predefined)

    return JSONResponse(success=False, error=error)
