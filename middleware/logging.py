import fastapi

import log

from .envelope import middleware_error_enveloped


@middleware_error_enveloped
async def middleware(request: fastapi.Request, call_next):
    log.info(f">> {request.method}\t{request.url.path}")
    try:
        return await call_next(request)
    finally:
        log.info(f"<< {request.method}\t{request.url.path}")
