from typing import NamedTuple

import fastapi
import starlette_context

import const
import log
from util import security
from util.tracker import get_request_time

from .envelope import middleware_error_enveloped


@middleware_error_enveloped
async def middleware(request: fastapi.Request, call_next):
    authed_account = None

    if auth_token := request.headers.get('auth-token', None):
        authed_account = security.decode_jwt(auth_token, time=get_request_time())  # Requires middleware.tracker
        log.info(f">>\tAuthed: {authed_account=}")

    starlette_context.context[const.CONTEXT_AUTHED_ACCOUNT_KEY] = authed_account
    return await call_next(request)


async def auth_header_placeholder(auth_token: str = fastapi.Header(None, convert_underscores=True)):
    """
    For injecting FastAPI's documentation
    """


# Dependency just for auto documentation purpose
doc_dependencies = [fastapi.Depends(auth_header_placeholder)]
