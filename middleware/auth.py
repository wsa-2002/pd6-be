from typing import NamedTuple

import fastapi
import starlette_context

from base.enum import RoleType
from persistence import database as db
import security

from . import common
from .tracker import get_request_time


class AuthedAccount(NamedTuple):  # Immutable
    id: int
    role: RoleType


class Middleware:
    """
    Base structure copied from https://www.starlette.io/authentication/
    """
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self.app(scope, receive, send)
            return

        request = fastapi.Request(scope)
        auth_token = request.headers.get('auth-token', None)
        if auth_token is None:
            authed_account = None
        else:
            account_id = security.decode_jwt(auth_token, time=get_request_time())  # Requires middleware.tracker
            authed_account = AuthedAccount(id=account_id, role=await db.rbac.read_global_role_by_account_id(account_id))

        starlette_context.context[common.AUTHED_ACCOUNT] = authed_account

        await self.app(scope, receive, send)


async def auth_header_placeholder(auth_token: str = fastapi.Header(None, convert_underscores=True)):
    """
    For injecting FastAPI's documentation
    """


# Dependency just for auto documentation purpose
doc_dependencies = [fastapi.Depends(auth_header_placeholder)]
