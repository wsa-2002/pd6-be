"""
Need middleware.tracker to take effect
"""
import uuid
from datetime import datetime
from typing import Optional

import starlette_context
import starlette_context.errors


REQUEST_UUID = 'REQUEST_UUID'
REQUEST_TIME = 'REQUEST_TIME'


def get_request_uuid() -> Optional[uuid.UUID]:
    try:
        return starlette_context.context[REQUEST_UUID]
    except starlette_context.errors.ContextDoesNotExistError:
        return None


def get_request_time() -> Optional[datetime]:
    try:
        return starlette_context.context[REQUEST_TIME]
    except starlette_context.errors.ContextDoesNotExistError:
        return None


def set_request_uuid(request_uuid: uuid.UUID):
    starlette_context.context[REQUEST_UUID] = request_uuid


def set_request_time(request_time: datetime):
    starlette_context.context[REQUEST_TIME] = request_time
