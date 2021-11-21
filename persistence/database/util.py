import json
from typing import Sequence, Iterable

from base.enum import FilterOperator
from base.popo import Filter
import log

from .base import FetchOne

ESTIMATE_COST_THRESHOLD = 5000000  # 65659969?


async def execute_count(sql: str, use_estimate_if_cost=0, use_estimate_if_rows=0, **kwargs) -> int:
    try:
        rows, cols, cost = await get_query_estimation(sql, **kwargs)
    except Exception as e:
        log.exception(e, msg='Execute count error', info_level=True)
    else:
        log.info(f'Query estimation is {rows=} {cols=} {cost=}')
        if cost > ESTIMATE_COST_THRESHOLD \
                or use_estimate_if_cost and cost > use_estimate_if_cost \
                or use_estimate_if_rows and rows > use_estimate_if_rows:
            log.info('Use estimation as count result')
            return rows

    return await get_query_actual_count(sql, **kwargs)


async def get_query_estimation(sql: str, **kwargs) -> tuple[int, int, int]:
    """
    Note: might raise IndexError or KeyError
    """
    async with FetchOne(
            event='get query estimation',
            sql=f"EXPLAIN (format json) {sql}",
            **kwargs,
    ) as (query_plan,):
        query_plan = json.loads(query_plan)
        # Note: might raise IndexError or KeyError in this part
        rows = query_plan[0]['Plan']['Plans'][0]['Plan Rows']
        cols = query_plan[0]['Plan']['Plans'][0]['Plan Width']
        cost = query_plan[0]['Plan']['Plans'][0]['Total Cost']
        return rows, cols, cost


async def get_query_actual_count(sql: str, **kwargs) -> int:
    async with FetchOne(
            event='get query count',
            sql=f"SELECT COUNT(*)"
                f"  FROM ({sql}) AS __COUNT_TABLE__",
            **kwargs,
    ) as (count,):
        return count


def _compile_filter(filter_: Filter, suffix='') -> tuple[str, dict]:  # sql, param_dict

    # Non-single values

    if filter_.op in (FilterOperator.in_, FilterOperator.not_in):
        value_dict = {fr'{filter_.col_name}_{filter_.op.name}{suffix}_{i}': val for i, val in enumerate(filter_.value)}
        if not value_dict:
            return ('FALSE' if filter_.op is FilterOperator.in_ else 'TRUE'), value_dict
        if len(value_dict) > 70:  # https://postgres.cz/wiki/PostgreSQL_SQL_Tricks_I#Predicate_IN_optimalization
            values = ', '.join(fr'(%({key})s)' for key in value_dict)
            return fr'{filter_.col_name} {filter_.op} (VALUES {values})', value_dict
        values = ', '.join(fr'%({key})s' for key in value_dict)
        return fr'{filter_.col_name} {filter_.op} ({values})', value_dict

    if filter_.op in (FilterOperator.between, FilterOperator.not_between):
        lb, ub = filter_.value
        value_dict = {
            fr'{filter_.col_name}_{filter_.op.name}{suffix}_lb': lb,
            fr'{filter_.col_name}_{filter_.op.name}{suffix}_ub': ub,
        }
        values = ' AND '.join(fr'%({k})s' for k in value_dict)
        return fr"{filter_.col_name} {filter_.op} {values}", value_dict

    # Single value

    param_name = fr"{filter_.col_name}_{filter_.op.name}{suffix}"
    sql = fr"{filter_.col_name} {filter_.op} %({param_name})s"

    if filter_.op in (FilterOperator.like, FilterOperator.not_like):
        return sql, {param_name: f'%{escape_pg_like_str(filter_.value)}%'}

    return sql, {param_name: filter_.value}


def compile_filters(filters: Sequence[Filter]) -> tuple[str, dict]:
    conditions, params = [], {}
    for i, filter_ in enumerate(filters):
        sql, param_dict = _compile_filter(filter_, suffix=str(i))
        conditions.append(sql)
        params |= param_dict

    return ' AND '.join(conditions), params


def compile_values(values: Iterable[Iterable]) -> tuple[str, list]:  # sql, param_list
    value_sql, params = [], []
    for items in values:
        value_sql.append(
            '('
            + ', '.join(f'${i}' for i, _ in enumerate(items, start=len(params) + 1))
            + ')'
        )
        params += list(items)

    sql = ', '.join(value_sql)
    return sql, params


def escape_pg_like_str(like_str: str) -> str:
    return like_str.replace('\\', '\\\\')
