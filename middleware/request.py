import datetime
import uuid

import fastapi
import starlette_context

import util.tracker
from base import do
import exceptions

from . import common


class Request(fastapi.Request):
    """
    This class is just for easy retrieval & type hinting, actual implementation relies on middleware
    """
    @property
    def account(self) -> do.Account:
        try:
            account = starlette_context.context[common.AUTHED_ACCOUNT]
        except KeyError:
            raise exceptions.SystemException("middleware.auth not used")
        else:
            if not account:
                raise exceptions.NoPermission
            return account

    @property
    def time(self) -> datetime.datetime:
        try:
            request_time = starlette_context.context[util.tracker.REQUEST_TIME]
        except KeyError:
            raise exceptions.SystemException("middleware.tracker not used")
        else:
            return request_time

    @property
    def uuid(self) -> uuid.UUID:
        try:
            request_uuid = starlette_context.context[util.tracker.REQUEST_UUID]
        except KeyError:
            raise exceptions.SystemException("middleware.tracker not used")
        else:
            return request_uuid
