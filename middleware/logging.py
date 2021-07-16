import fastapi

import log

from .util import get_request_body


async def middleware(request: fastapi.Request, call_next):
    request_body = await get_request_body(request)

    log.info(f">> {request.method}\t{request.url.path}\tQuery: {request.query_params}\tBody: {request_body}")

    response = await call_next(request)

    if isinstance(response, fastapi.responses.JSONResponse):
        log.info(f"<< {request.method}\t{request.url.path}\tJSON body: {response.body}")
    else:
        log.info(f"<< {request.method}\t{request.url.path}")

    return response
