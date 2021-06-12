import datetime
import json
import typing

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

    @log.timed
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
    is_predefined = isinstance(error, exceptions.PdogsException)
    log.exception(error, info_level=is_predefined)

    return JSONResponse(success=False, error=error)
