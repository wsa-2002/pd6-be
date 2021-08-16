from datetime import datetime
from typing import Sequence, Optional

from base import do

from .base import SafeExecutor


async def add(receiver: str, grader: str, class_id: int, title: str, score: Optional[str], comment: Optional[str],
              update_time: datetime) -> int:
    async with SafeExecutor(
            event='Add grade',
            sql=r'INSERT INTO grade'
                r'            (receiver_id, grader_id, class_id, title, score, comment,'
                r'             update_time)'
                r'     VALUES (account_referral_to_id(%(receiver)s), account_referral_to_id(%(grader)s), %(class_id)s,'
                r'             %(title)s, %(score)s, %(comment)s, %(update_time)s)'
                r'  RETURNING id',
            receiver=receiver, grader=grader, class_id=class_id, title=title, score=score, comment=comment,
            update_time=update_time,
            fetch=1,
    ) as (grade_id,):
        return grade_id


async def browse(class_id: int = None, receiver_id: int = None,
                 include_deleted=False) -> Sequence[do.Grade]:
    conditions = {}
    if class_id is not None:
        conditions['class_id'] = class_id
    if receiver_id is not None:
        conditions['receiver_id'] = receiver_id

    filters = []
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(list(fr"{field_name} = %({field_name})s" for field_name in conditions)
                            + filters)

    async with SafeExecutor(
            event='browse grades',
            sql=fr'SELECT id, receiver_id, grader_id, class_id,'
                fr'       title, score, comment, update_time, is_deleted'
                fr'  FROM grade'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY class_id ASC, id ASC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id,
                         title=title, score=score, comment=comment, update_time=update_time,
                         is_deleted=is_deleted)
                for (id_, receiver_id, grader_id, class_id,
                     title, score, comment, update_time, is_deleted)
                in records]


async def read(grade_id: int, include_deleted=False) -> do.Grade:
    async with SafeExecutor(
            event='read grade',
            sql=fr'SELECT id, receiver_id, grader_id, class_id, title, score, comment, update_time,'
                fr'       is_deleted'
                fr'  FROM grade'
                fr' WHERE id = %(grade_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            grade_id=grade_id,
            fetch=1,
    ) as (id_, receiver_id, grader_id, class_id, title, score, comment, update_time, is_deleted):
        return do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id, title=title,
                        score=score, comment=comment, update_time=update_time,
                        is_deleted=is_deleted)


async def edit(grade_id: int, update_time: datetime, title: str = None, score: Optional[str] = ...,
               comment: Optional[str] = ...) -> None:
    to_updates = {
        'update_time': update_time,
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

    async with SafeExecutor(
            event='update grade by id',
            sql=fr'UPDATE grade'
                fr'   SET {set_sql}'
                fr' WHERE id = %(grade_id)s',
            grade_id=grade_id,
            **to_updates,
    ):
        pass


async def delete(grade_id: int) -> None:
    async with SafeExecutor(
            event='soft delete team',
            sql=fr'UPDATE grade'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(grade_id)s',
            grade_id=grade_id,
            is_deleted=True,
    ):
        pass
