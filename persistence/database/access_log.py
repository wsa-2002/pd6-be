from datetime import datetime
from typing import Optional, Sequence

from base import do

from .base import SafeExecutor


async def add(access_time: datetime, request_method: str, resource_path: str, ip: str, account_id: int) -> int:
    async with SafeExecutor(
            event='Add access_log',
            sql="INSERT INTO access_log"
                "            (access_time, request_method, resource_path, ip, account_id)"
                "     VALUES (%(access_time)s, %(request_method)s, %(resource_path)s, %(ip)s, %(account_id)s)"
                "  RETURNING id",
            access_time=access_time, request_method=request_method, resource_path=resource_path, ip=ip, account_id=account_id,
            fetch=1,
    ) as (id_,):
        return id_


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
