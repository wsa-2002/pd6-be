from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from itertools import chain

import fastapi
import jwt

from base.cls import DataclassBase
from base.enum import RoleType
import exceptions as exc
from persistence import database as db


SECRET = 'aaa'  # TODO
DEFAULT_VALID = timedelta(days=7)  # TODO


@dataclass
class Account(DataclassBase):
    id: int
    role: RoleType


async def gen_jwt(account_id: int, expire: timedelta = DEFAULT_VALID) -> str:
    return jwt.encode({
        'account-id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
    }, key=SECRET)


async def validate_jwt(encoded: str) -> Account:
    decoded = jwt.decode(encoded, key=SECRET)
    expire = datetime.fromisoformat(decoded['expire'])
    if expire > datetime.now():
        raise exc.LoginExpired
    account_id = decoded['account-id']
    return Account(id=account_id, role=await db.rbac.get_system_role_by_account_id(account_id))


class Middleware:
    """
    Base structure copied from https://www.starlette.io/authentication/
    """
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            return

        try:
            assert scope["type"] in ["http", "websocket"]
        except AssertionError:
            return
        else:
            request = fastapi.Request(scope)
            auth_token = request.headers.get('auth-token', None)
            if authed_account := await validate_jwt(auth_token):
                scope['authed_account'] = authed_account
        finally:
            await self.app(scope, receive, send)


class Request(fastapi.Request):
    @property
    def account(self) -> Account:
        try:
            return self.scope['authed_account']
        except KeyError:
            raise exc.NoPermission
