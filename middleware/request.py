import datetime
import uuid

import fastapi
import starlette_context

import const
import util.tracker
import util.security
import exceptions


class Request(fastapi.Request):
    """
    This class is just for easy retrieval & type hinting, actual implementation relies on middleware
    """
    @property
    def account(self) -> util.security.AuthedAccount:
        try:
            account = starlette_context.context[const.CONTEXT_AUTHED_ACCOUNT_KEY]
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
