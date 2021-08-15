from datetime import datetime
from typing import Optional, Sequence

from base import do
from base.popo import Filter
import exceptions as exc
import log

from .base import SafeExecutor
from .util import execute_count, compile_filters


async def add(access_time: datetime, request_method: str, resource_path: str, ip: str, account_id: Optional[int]) \
        -> int:
    async with SafeExecutor(
            event='Add access_log',
            sql="INSERT INTO access_log"
                "            (access_time, request_method, resource_path, ip, account_id)"
                "     VALUES (%(access_time)s, %(request_method)s, %(resource_path)s, %(ip)s, %(account_id)s)"
                "  RETURNING id",
            access_time=access_time, request_method=request_method, resource_path=resource_path,
            ip=ip, account_id=account_id,
            fetch=1,
    ) as (id_,):
        return id_


async def browse(
        limit: int, offset: int,
        access_time: Sequence[Filter] = (),
        request_method: Sequence[Filter] = (),
        resource_path: Sequence[Filter] = (),
        ip: Sequence[Filter] = (),
        account_id: Sequence[Filter] = (),
) -> tuple[Sequence[do.AccessLog], int]:

    cond_sql, cond_params = compile_filters(
        access_time=access_time,
        request_method=request_method,
        resource_path=resource_path,
        ip=ip,
        account_id=account_id,
    )

    async with SafeExecutor(
            event='browse access_logs',
            sql=fr'SELECT id, access_time, request_method, resource_path, ip, account_id'
                fr'  FROM access_log'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,
    ) as records:
        data = [do.AccessLog(id=id_, access_time=access_time, request_method=request_method,
                             resource_path=resource_path, ip=ip, account_id=account_id)
                for id_, access_time, request_method, resource_path, ip, account_id
                in records]

    total_count = await execute_count(
        sql=fr'SELECT id, access_time, request_method, resource_path, ip, account_id'
            fr'  FROM access_log'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count
