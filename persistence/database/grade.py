from datetime import datetime
from typing import Sequence, Optional

from base import do

from .base import SafeExecutor


async def add(receiver_id: int, grader_id: int, class_id: int, title: str,
              score: Optional[int], comment: Optional[str], is_hidden: bool, is_deleted: bool,
              update_time: Optional[datetime] = None) -> int:
    if update_time is None:
        update_time = datetime.now()

    async with SafeExecutor(
            event='Add grade',
            sql=r'INSERT INTO grade'
                r'            (receiver_id, grader_id, class_id,'
                r'             title, score, comment, update_time,'
                r'             is_hidden, is_deleted)'
                r'     VALUES (%(receiver_id)s, %(grader_id)s, %(class_id)s,'
                r'             %(title)s, %(score)s, %(comment)s, %(update_time)s,'
                r'             %(is_hidden)s, %(is_deleted)s)'
                r'  RETURNING id',
            receiver_id=receiver_id, grader_id=grader_id, class_id=class_id,
            title=title, score=score, comment=comment, update_time=update_time,
            is_hidden=is_hidden, is_deleted=is_deleted,
            fetch=1,
    ) as (grade_id,):
        return grade_id


async def browse(class_id: int = None, account_id: int = None,
                 include_hidden=False, include_deleted=False) -> Sequence[do.Grade]:
    conditions = {}
    if class_id is not None:
        conditions['class_id'] = class_id
    if account_id is not None:
        conditions['account_id'] = account_id

    filters = []
    if not include_hidden:
        filters.append("NOT is_hidden")
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(list(fr"{field_name} = %({field_name})s" for field_name in conditions)
                            + filters)

    async with SafeExecutor(
            event='browse grades',
            sql=fr'SELECT id, receiver_id, grader_id, class_id,'
                fr'       title, score, comment, update_time, is_hidden, is_deleted'
                fr'  FROM grade'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY class_id ASC, id ASC',
            **conditions,
            fetch='all',
    ) as records:
        return [do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id,
                         title=title, score=score, comment=comment, update_time=update_time,
                         is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, receiver_id, grader_id, class_id,
                     title, score, comment, update_time, is_hidden, is_deleted)
                in records]


async def read(grade_id: int, include_hidden=False, include_deleted=False) -> do.Grade:
    async with SafeExecutor(
            event='read grade',
            sql=fr'SELECT id, receiver_id, grader_id, class_id, title, score, comment, update_time,'
                fr'       is_hidden, is_deleted'
                fr'  FROM grade'
                fr' WHERE id = %(grade_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            grade_id=grade_id,
            fetch=1,
    ) as (id_, receiver_id, grader_id, class_id, title, score, comment, update_time, is_hidden, is_deleted):
        return do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id, title=title,
                        score=score, comment=comment, update_time=update_time,
                        is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(grade_id: int, title: Optional[str], score: Optional[int], comment: Optional[str],
               update_time: Optional[datetime] = None, is_hidden: bool = None) -> None:
    if update_time is None:
        update_time = datetime.now()

    to_updates = {}

    if title is not None:
        to_updates['title'] = title
    if score is not None:
        to_updates['score'] = score
    if comment is not None:
        to_updates['comment'] = comment
    if update_time is not None:
        to_updates['update_time'] = update_time
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

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
