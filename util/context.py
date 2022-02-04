import datetime
import uuid

import starlette_context

from base import mcs
import exceptions

from . import security


class Context(metaclass=mcs.Singleton):
    _context = starlette_context.context

    CONTEXT_AUTHED_ACCOUNT_KEY = 'AUTHED_ACCOUNT'
    REQUEST_UUID = 'REQUEST_UUID'
    REQUEST_TIME = 'REQUEST_TIME'

    def set_account(self, account: security.AuthedAccount):
        self._context[self.CONTEXT_AUTHED_ACCOUNT_KEY] = account

    def get_account(self) -> security.AuthedAccount | None:
        return self._context.get(self.CONTEXT_AUTHED_ACCOUNT_KEY) if self._context.exists() else None

    @property
    def account(self) -> security.AuthedAccount:
        try:
            account = self._context[self.CONTEXT_AUTHED_ACCOUNT_KEY]
        except KeyError:
            raise exceptions.SystemException("middleware.auth not used")
        else:
            if not account:
                raise exceptions.NoPermission
            return account

    def set_request_time(self, time: datetime.datetime):
        self._context[self.REQUEST_TIME] = time

    def get_request_time(self) -> datetime.datetime | None:
        return self._context.get(self.REQUEST_TIME) if self._context.exists() else None

    @property
    def request_time(self) -> datetime.datetime:
        try:
            request_time = self._context[self.REQUEST_TIME]
        except KeyError:
            raise exceptions.SystemException("middleware.tracker not used")
        else:
            return request_time

    def set_request_uuid(self, uuid_: uuid.UUID):
        self._context[self.REQUEST_UUID] = uuid_

    def get_request_uuid(self) -> uuid.UUID | None:
        return self._context.get(self.REQUEST_UUID) if self._context.exists() else None

    @property
    def request_uuid(self) -> uuid.UUID:
        try:
            request_uuid = self._context[self.REQUEST_UUID]
        except KeyError:
            raise exceptions.SystemException("middleware.tracker not used")
        else:
            return request_uuid


context = Context()
