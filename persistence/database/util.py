from typing import Sequence

from base.enum import FilterOperator
from base.popo import Filter
import log

from .base import SafeExecutor


ESTIMATE_COST_THRESHOLD = 5000000  # 65659969?


async def execute_count(sql: str, **kwargs) -> int:
    try:
        rows, cols, cost = await get_query_estimation(sql, **kwargs)
    except:
        log.info('Execute count error, pass')
    else:
        if cost > ESTIMATE_COST_THRESHOLD:
            return rows

    return await get_query_actual_count(sql, **kwargs)


async def get_query_estimation(sql: str, **kwargs) -> tuple[int, int, int]:
    """
    Note: might raise IndexError or KeyError
    """
    async with SafeExecutor(
            event='get query estimation',
            sql=f"EXPLAIN (format json) {sql}",
            **kwargs,
            fetch=1,
    ) as (query_plan,):
        # Note: might raise IndexError or KeyError in this part
        rows = query_plan[0]['Plan']['Plan Rows']
        cols = query_plan[0]['Plan']['Plan Width']
        cost = query_plan[0]['Plan']['Total Cost']
        return rows, cols, cost


async def get_query_actual_count(sql: str, **kwargs) -> int:
    async with SafeExecutor(
            event='get query count',
            sql=f"SELECT COUNT(*)"
                f"  FROM ({sql}) AS __COUNT_TABLE__",
            **kwargs,
            fetch=1,
    ) as (count,):
        return count


def _compile_filter(filter_: Filter, suffix='') -> tuple[str, dict]:  # sql, param_dict

    # Non-single values

    if filter_.op in (FilterOperator.in_, FilterOperator.not_in):
        value_dict = {fr'{filter_.col_name}_{filter_.op.name}{suffix}_{i}': val for i, val in enumerate(filter_.value)}
        if len(value_dict) > 70:  # https://postgres.cz/wiki/PostgreSQL_SQL_Tricks_I#Predicate_IN_optimalization
            values = ', '.join(fr'(%({key})s)' for key in value_dict)
            return fr'{filter_.col_name} {filter_.op} (VALUES {values})', value_dict
        else:
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
        return sql, {param_name: f'%{filter_.value}%'}

    return sql, {param_name: filter_.value}


def compile_filters(filters: Sequence[Filter]) -> tuple[str, dict]:
    conditions, params = [], {}
    for i, filter_ in enumerate(filters):
        sql, param_dict = _compile_filter(filter_, suffix=str(i))
        conditions.append(sql)
        params |= param_dict

    return ' AND '.join(conditions), params
