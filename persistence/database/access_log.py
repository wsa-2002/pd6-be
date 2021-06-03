from datetime import datetime
from typing import Optional, Sequence

from base import do

from .base import SafeExecutor


async def browse(offset: int = 0, limit: int = 50) -> Sequence[do.AccessLog]:
    async with SafeExecutor(
            event='browse access_logs',
            sql=fr'SELECT id, access_time, request_method, resource_path, ip, account_id'
                fr'  FROM access_log'
                fr' ORDER BY id ASC'
                fr' OFFSET {offset} LIMIT {limit}',
            fetch='all',
    ) as records:
        return [do.AccessLog(id=id_, access_time=access_time, request_method=request_method,
                             resource_path=resource_path, ip=ip, account_id=account_id)
                for id_, access_time, request_method, resource_path, ip, account_id
                in records]
