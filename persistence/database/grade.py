from datetime import datetime
from typing import Sequence, Optional

import asyncpg

from base import do, enum
from base.popo import Filter, Sorter
import exceptions as exc

from .base import AutoTxConnection, OnlyExecute, FetchOne, FetchAll, ParamDict
from .util import execute_count, compile_filters, compile_values
from .account import account_referral_to_id


async def add(receiver: str, grader: str, class_id: int, title: str, score: Optional[str], comment: Optional[str],
              update_time: datetime) -> int:
    async with FetchOne(
            event='Add grade',
            sql=r'INSERT INTO grade'
                r'            (receiver_id, grader_id, class_id, title, score, comment,'
                r'             update_time)'
                r'     VALUES (account_referral_to_id(%(receiver)s), account_referral_to_id(%(grader)s), %(class_id)s,'
                r'             %(title)s, %(score)s, %(comment)s, %(update_time)s)'
                r'  RETURNING id',
            receiver=receiver, grader=grader, class_id=class_id, title=title, score=score, comment=comment,
            update_time=update_time,
    ) as (grade_id,):
        return grade_id


async def batch_add(class_id: int, title: str, grades: Sequence[tuple[str, str, str, str]], update_time: datetime):
    # grade in grades : receiver, score, comment, grader
    values = [(await account_referral_to_id(receiver),
               score,
               comment,
               await account_referral_to_id(grader),
               class_id,
               title,
               update_time)
              for receiver, score, comment, grader in grades]

    value_sql, value_params = compile_values(values)

    async with AutoTxConnection(event=f'batch import grade into class {class_id}') as conn:
        try:
            await conn.execute(fr' INSERT INTO grade'
                               fr'             (receiver_id, score, comment, grader_id, class_id, title, update_time)'
                               fr'      VALUES {value_sql}'
                               fr' ON CONFLICT (class_id, receiver_id, title)'
                               fr'             WHERE NOT is_deleted'
                               fr'   DO UPDATE'
                               fr'         SET score = EXCLUDED.score,'
                               fr'             comment = EXCLUDED.comment,'
                               fr'             grader_id = EXCLUDED.grader_id,'
                               fr'             update_time = EXCLUDED.update_time',
                               *value_params)
        except asyncpg.exceptions.UniqueViolationError:
            raise exc.persistence.UniqueViolationError


async def browse(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter]) \
        -> tuple[Sequence[do.Grade], int]:

    filters += [Filter(col_name='is_deleted',
                       op=enum.FilterOperator.eq,
                       value=False)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse grades',
            sql=fr'SELECT id, receiver_id, grader_id, class_id,'
                fr'       title, score, comment, update_time, is_deleted'
                fr'  FROM grade'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} class_id ASC, id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id,
                         title=title, score=score, comment=comment, update_time=update_time,
                         is_deleted=is_deleted)
                for (id_, receiver_id, grader_id, class_id,
                     title, score, comment, update_time, is_deleted)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT id, receiver_id, grader_id, class_id,'
            fr'       title, score, comment, update_time, is_deleted'
            fr'  FROM grade'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def read(grade_id: int, include_deleted=False) -> do.Grade:
    async with FetchOne(
            event='read grade',
            sql=fr'SELECT id, receiver_id, grader_id, class_id, title, score, comment, update_time,'
                fr'       is_deleted'
                fr'  FROM grade'
                fr' WHERE id = %(grade_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            grade_id=grade_id,
    ) as (id_, receiver_id, grader_id, class_id, title, score, comment, update_time, is_deleted):
        return do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id, title=title,
                        score=score, comment=comment, update_time=update_time,
                        is_deleted=is_deleted)


async def edit(grade_id: int, grader_id: int, update_time: datetime, title: str = None, score: Optional[str] = ...,
               comment: Optional[str] = ...) -> None:
    to_updates: ParamDict = {
        'update_time': update_time,
        'grader_id': grader_id
    }

    if title is not None:
        to_updates['title'] = title
    if score is not ...:
        to_updates['score'] = score
    if comment is not ...:
        to_updates['comment'] = comment

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='update grade by id',
            sql=fr'UPDATE grade'
                fr'   SET {set_sql}'
                fr' WHERE id = %(grade_id)s',
            grade_id=grade_id,
            **to_updates,
    ):
        pass


async def delete(grade_id: int) -> None:
    async with OnlyExecute(
            event='soft delete team',
            sql=r'UPDATE grade'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(grade_id)s',
            grade_id=grade_id,
            is_deleted=True,
    ):
        pass
