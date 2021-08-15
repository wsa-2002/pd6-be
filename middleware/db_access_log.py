import fastapi
import starlette_context

import persistence.database as db
from util import tracker

from . import common
from .envelope import middleware_error_enveloped


@middleware_error_enveloped
async def middleware(request: fastapi.Request, call_next):
    account = starlette_context.context.get(common.AUTHED_ACCOUNT, None)
    await db.access_log.add(
        access_time=tracker.get_request_time(),
        request_method=request.method,
        resource_path=request.url.path,
        ip=request.client.host,
        account_id=account.id if account else None,
    )
    return await call_next(request)
