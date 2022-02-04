from datetime import datetime
import uuid

import fastapi

from util.context import context

from .envelope import middleware_error_enveloped


@middleware_error_enveloped
async def middleware(request, call_next):
    request_uuid, request_time = uuid.uuid1(), datetime.now()
    context.set_request_uuid(request_uuid)
    context.set_request_time(request_time)

    response: fastapi.Response = await call_next(request)
    response.headers['X-Request-ID'] = str(request_uuid)
    return response
