from datetime import datetime
from typing import Optional, Sequence

from base import do
from base.popo import Filter, Sorter

from .base import FetchOne, FetchAll
from .util import execute_count, compile_filters


async def add(access_time: datetime, request_method: str, resource_path: str, ip: str, account_id: Optional[int]) \
        -> int:
    async with FetchOne(
            event='Add access_log',
            sql="INSERT INTO access_log"
                "            (access_time, request_method, resource_path, ip, account_id)"
                "     VALUES (%(access_time)s, %(request_method)s, %(resource_path)s, %(ip)s, %(account_id)s)"
                "  RETURNING id",
            access_time=access_time, request_method=request_method, resource_path=resource_path,
            ip=ip, account_id=account_id,
    ) as (id_,):
        return id_


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[do.AccessLog], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse access_logs',
            sql=fr'SELECT id, access_time, request_method, resource_path, ip, account_id'
                fr'  FROM access_log'
                fr' INNER JOIN (SELECT id'
                fr'             FROM access_log'
                fr'{f"          WHERE {cond_sql}" if cond_sql else ""}'
                fr'             ORDER BY {sort_sql} id ASC'
                fr'             LIMIT %(limit)s OFFSET %(offset)s'
                fr'            ) filtered_access_log(access_log_id)'
                fr'         ON filtered_access_log.access_log_id = access_log.id'
                fr' ORDER BY {sort_sql} id ASC',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.AccessLog(id=id_, access_time=access_time, request_method=request_method,
                             resource_path=resource_path, ip=ip, account_id=account_id)
                for id_, access_time, request_method, resource_path, ip, account_id
                in records]

    total_count = await execute_count(
        sql=fr'SELECT id'
            fr'  FROM access_log'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count
