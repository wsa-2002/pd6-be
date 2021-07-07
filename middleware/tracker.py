from datetime import datetime
from typing import Optional
import uuid

import starlette_context
import starlette_context.errors


async def middleware(request, call_next):
    starlette_context.context['request_id'] = uuid.uuid1()
    starlette_context.context['request_time'] = datetime.now()
    return await call_next(request)


def get_request_uuid() -> Optional[uuid.UUID]:
    try:
        return starlette_context.context['request_id']
    except starlette_context.errors.ContextDoesNotExistError:
        return None


def get_request_time() -> Optional[datetime]:
    try:
        return starlette_context.context['request_time']
    except starlette_context.errors.ContextDoesNotExistError:
        return None
