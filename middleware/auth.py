from dataclasses import dataclass
from typing import Callable

import fastapi

from base.cls import DataclassBase
from base.enum import RoleType
import exceptions as exc
from persistence import database as db
from util import jwt


@dataclass
class Account(DataclassBase):
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
        if auth_token and (account_id := await jwt.decode(auth_token)):
            scope['authed_account'] = Account(id=account_id,
                                              role=await db.rbac.get_global_role_by_account_id(account_id))
        await self.app(scope, receive, send)


class Request(fastapi.Request):
    @property
    def account(self) -> Account:
        try:
            return self.scope['authed_account']
        except KeyError:
            raise exc.NoPermission


class APIRoute(fastapi.routing.APIRoute):
    """
    An `APIRoute` class that swaps the request class to auth.Request,
    providing client login status auto-verification with `Request.account` property.
    """
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: fastapi.Request) -> fastapi.Response:
            request = Request(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler
