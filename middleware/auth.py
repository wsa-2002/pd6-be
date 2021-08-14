from typing import NamedTuple

import fastapi
import starlette_context

from base.enum import RoleType
import log
from persistence import database as db
from util import security
from util.tracker import get_request_time

from . import common
from .envelope import middleware_error_enveloped


class AuthedAccount(NamedTuple):  # Immutable
    id: int
    role: RoleType


@middleware_error_enveloped
async def middleware(request: fastapi.Request, call_next):
    authed_account = None

    if auth_token := request.headers.get('auth-token', None):
        account_id = security.decode_jwt(auth_token, time=get_request_time())  # Requires middleware.tracker
        authed_account = AuthedAccount(id=account_id, role=await db.rbac.read_global_role_by_account_id(account_id))
        log.info(f">>\tAuthed: {account_id=}")

    starlette_context.context[common.AUTHED_ACCOUNT] = authed_account
    return await call_next(request)


async def auth_header_placeholder(auth_token: str = fastapi.Header(None, convert_underscores=True)):
    """
    For injecting FastAPI's documentation
    """


# Dependency just for auto documentation purpose
doc_dependencies = [fastapi.Depends(auth_header_placeholder)]
