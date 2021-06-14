import fastapi

import log
from . import envelope


async def middleware(request: fastapi.Request, call_next):
    log.info(f">> {request.method}\t{request.url.path}\tBody: {await request.body()}")

    response = await call_next(request)

    if isinstance(response, envelope.JSONResponse):
        log.info(f"<< {request.method}\t{request.url.path}\tJSON body: {response.body}")
    else:
        log.info(f"<< {request.method}\t{request.url.path}")

    return response
