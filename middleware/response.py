import datetime
import json
import typing
from uuid import UUID

import fastapi.responses


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.astimezone().isoformat()  # Return with timezone
        elif isinstance(obj, UUID):
            return str(obj)

        return super().default(obj)


class JSONResponse(fastapi.responses.JSONResponse):
    def __init__(self, *args, success=True, error: Exception = None, **kwargs):
        self._success = success
        self._error = error
        super().__init__(*args, **kwargs)

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            cls=JSONEncoder,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
