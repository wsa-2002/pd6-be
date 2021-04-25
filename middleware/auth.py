from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

import fastapi
from fastapi import routing
import jwt

from base.cls import DataclassBase
from base.enum import RoleType
from persistence.database.rbac import get_system_role_by_account_id


SECRET = 'aaa'  # TODO
DEFAULT_VALID = timedelta(days=7)  # TODO


@dataclass
class AuthedAccount(DataclassBase):
    id: int
    role: RoleType


class AuthedRequest(fastapi.Request):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO
        encoded_jwt = self.headers.get('auth-token')
        try:
            self._account = decode_jwt(encoded_jwt)
        except:
            ...  # TODO

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


def gen_jwt(account_id: int, expire: timedelta = DEFAULT_VALID) -> str:
    return jwt.encode({
        'account-id': account_id,
        'expire': (datetime.now() + expire).isoformat(),
    }, key=SECRET)


def decode_jwt(encoded: str) -> AuthedAccount:
    decoded = jwt.decode(encoded, key=SECRET)
    expire = datetime.fromisoformat(decoded['expire'])
    if expire > datetime.now():
        ...  # TODO
    account_id = decoded['account-id']
    return AuthedAccount(id=account_id, role=await get_system_role_by_account_id(account_id))
