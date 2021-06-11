from datetime import datetime
from util import get_request_uuid

import fastapi

import log
from . import envelope


async def middleware(request: fastapi.Request, call_next):
    request_uuid = get_request_uuid()

    log.info(f">> {request.method} {request.url.path}")
    log.info(f">> Body: {await request.body()}")

    response = await call_next(request)

    log.info(f"<< {request.method} {request.url.path}")
    if isinstance(response, envelope.JSONResponse):
        log.info(f"<< {request_uuid}\tJSON body: {response.body}")

    return response
