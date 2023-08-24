import fastapi
import starlette_context

import const
import log
import persistence.database as db
from util.context import context

from .envelope import middleware_error_enveloped


@middleware_error_enveloped
async def middleware(request: fastapi.Request, call_next):
    account = starlette_context.context.get(const.CONTEXT_AUTHED_ACCOUNT_KEY, None)
    # try to clarify the root cause of issue #295 (request with no ip)
    if not request.client.host:
        log.info(f'Request header: {request.headers}')
        log.info(f'Request client: {request.client}')
    await db.access_log.add(
        access_time=context.request_time,
        request_method=request.method,
        resource_path=request.url.path,
        ip=request.client.host,
        account_id=account.id if account else None,
    )
    return await call_next(request)
