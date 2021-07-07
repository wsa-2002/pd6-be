import fastapi

import log


async def middleware(request: fastapi.Request, call_next):
    log.info(f">> {request.method}\t{request.url.path}\tQuery: {request.query_params}\tBody: {await request.body()}")

    response = await call_next(request)

    if isinstance(response, fastapi.responses.JSONResponse):
        log.info(f"<< {request.method}\t{request.url.path}\tJSON body: {response.body}")
    else:
        log.info(f"<< {request.method}\t{request.url.path}")

    return response
