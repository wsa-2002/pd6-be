from datetime import datetime
from typing import Optional
import uuid

import fastapi
import starlette_context
import starlette_context.errors

from . import common


async def middleware(request, call_next):
    starlette_context.context[common.REQUEST_UUID] = request_uuid = uuid.uuid1()
    starlette_context.context[common.REQUEST_TIME] = datetime.now()
    response: fastapi.Response = await call_next(request)
    response.headers['X-Request-ID'] = str(request_uuid)
    return response


def get_request_uuid() -> Optional[uuid.UUID]:
    try:
        return starlette_context.context[common.REQUEST_UUID]
    except starlette_context.errors.ContextDoesNotExistError:
        return None


def get_request_time() -> Optional[datetime]:
    try:
        return starlette_context.context[common.REQUEST_TIME]
    except starlette_context.errors.ContextDoesNotExistError:
        return None
