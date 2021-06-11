import datetime
import json
import typing

import exceptions as exc

import fastapi.exceptions
import fastapi.routing


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


async def exception_handler(request, error: Exception):
    # Convert Pydantic's ValidationError to self-defined error
    if isinstance(error, fastapi.exceptions.ValidationError):
        error = exc.IllegalInput(cause=error)

    return JSONResponse(success=False, error=error)
