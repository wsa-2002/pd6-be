from functools import wraps
from itertools import chain

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import fastapi
from fastapi import routing
import jwt

import exceptions as exc
from base.cls import DataclassBase
from base.enum import RoleType
from persistence import database as db


SECRET = 'aaa'  # TODO
DEFAULT_VALID = timedelta(days=7)  # TODO


@dataclass
class AuthedAccount(DataclassBase):
    id: int
    role: RoleType


def gen_jwt(account_id: int, expire: timedelta = DEFAULT_VALID) -> str:
    return jwt.encode({
        'account-id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
    }, key=SECRET)


def validate_jwt(encoded: str) -> AuthedAccount:
    decoded = jwt.decode(encoded, key=SECRET)
    expire = datetime.fromisoformat(decoded['expire'])
    if expire > datetime.now():
        raise exc.LoginExpired
    account_id = decoded['account-id']
    return AuthedAccount(id=account_id, role=await db.rbac.get_system_role_by_account_id(account_id))


class AuthedRequest(fastapi.Request):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            encoded_jwt = self.headers['auth-token']
        except KeyError:
            raise exc.NoPermission

        self._account = validate_jwt(encoded_jwt)

    @property
    def account(self) -> AuthedAccount:
        return self._account


class LoginRequiredRouter(routing.APIRoute):
    """
    An `APIRoute` class that swaps the request class to auth.Request,
    providing client login status auto-verification with `Request.account` property.
    """
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: fastapi.Request) -> fastapi.Response:
            request = AuthedRequest(request.scope, request.receive)
            return await original_route_handler(request)

        return custom_route_handler


def require_normal(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        # find authed request
        for arg in chain(args, kwargs.values()):
            if isinstance(arg, AuthedRequest):
                if arg.account.role < RoleType.normal:
                    raise exc.NoPermission
                break
        else:
            raise ValueError("Unable to find authed request in function's arguments")

        return func(*args, **kwargs)


def require_manager(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        # find authed request
        for arg in chain(args, kwargs.values()):
            if isinstance(arg, AuthedRequest):
                if arg.account.role < RoleType.manager:
                    raise exc.NoPermission
                break
        else:
            raise ValueError("Unable to find authed request in function's arguments")

        return func(*args, **kwargs)
