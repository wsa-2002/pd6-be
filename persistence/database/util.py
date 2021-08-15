from typing import Sequence

from base.enum import FilterOperator
from base.popo import Filter

from .base import SafeExecutor


async def count(table_name: str) -> int:
    async with SafeExecutor(
            event=f'count {table_name=}',
            sql=fr'SELECT COUNT(*)'
                fr'  FROM {table_name}',
            fetch=1,
    ) as (count_,):
        return count_


def _compile_filter(col_name: str, filter_: Filter, suffix='') -> tuple[str, dict]:  # sql, param_dict

    # Non-single values

    if filter_.op in (FilterOperator.in_, FilterOperator.not_in):
        value_dict = {fr'{col_name}_{filter_.op.name}{suffix}_{i}': val for i, val in enumerate(filter_.val)}
        if len(value_dict) > 70:  # https://postgres.cz/wiki/PostgreSQL_SQL_Tricks_I#Predicate_IN_optimalization
            values = ', '.join(fr'(%({key})s)' for key in value_dict)
            return fr'{col_name} {filter_.op} (VALUES {values})', value_dict
        else:
            values = ', '.join(fr'%({key})s' for key in value_dict)
            return fr'{col_name} {filter_.op} ({values})', value_dict

    if filter_.op in (FilterOperator.between, FilterOperator.not_between):
        lb, ub = filter_.val
        value_dict = {
            fr'{col_name}_{filter_.op.name}{suffix}_lb': lb,
            fr'{col_name}_{filter_.op.name}{suffix}_ub': ub,
        }
        values = ' AND '.join(fr'%({k})s' for k in value_dict)
        return fr"{col_name} {filter_.op} {values}", value_dict

    # Single value

    param_name = fr"{col_name}_{filter_.op.name}{suffix}"
    sql = fr"{col_name} {filter_.op} %({param_name})s"

    if filter_.op in (FilterOperator.like, FilterOperator.not_like):
        return sql, {param_name: f'%{filter_.val}%'}

    return sql, {param_name: filter_.val}


def compile_filters(**col_filters: Sequence[Filter]) -> tuple[str, dict]:
    conditions, params = [], {}
    for col_name, filters in col_filters.items():
        for i, filter_ in enumerate(filters):
            sql, param_dict = _compile_filter(col_name, filter_, suffix=str(i))
            conditions.append(sql)
            params |= param_dict

    return ' AND '.join(conditions), params
