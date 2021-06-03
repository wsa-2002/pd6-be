from datetime import datetime
from typing import Sequence, Optional

from base import do

from .base import SafeExecutor


async def add(receiver_id: int, grader_id: int, class_id: int, title: str,
              score: Optional[int], comment: Optional[str], update_time: Optional[datetime] = None) -> int:
    if update_time is None:
        update_time = datetime.now()

    async with SafeExecutor(
            event='Add grade',
            sql=r'INSERT INTO grade'
                r'            (receiver_id, grader_id, class_id, title, score, comment, update_time)'
                r'     VALUES (%(name)s, %(email_domain)s)'
                r'  RETURNING id',
            receiver_id=receiver_id, grader_id=grader_id, class_id=class_id, title=title,
            score=score, comment=comment, update_time=update_time,
            fetch=1,
    ) as (grade_id,):
        return grade_id


async def browse(class_id: int = None, account_id: int = None) -> Sequence[do.Grade]:
    conditions = {}

    if class_id is not None:
        conditions['class_id'] = class_id
    if account_id is not None:
        conditions['account_id'] = account_id

    cond_sql = ' AND '.join(fr"{field_name} = %({field_name})s" for field_name in conditions)

    async with SafeExecutor(
            event='browse grades',
            sql=fr'SELECT id, receiver_id, grader_id, class_id, title, score, comment, update_time'
                fr'  FROM grade'
                fr' {f"WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY class_id ASC, id ASC',
            fetch='all',
    ) as records:
        return [do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id, title=title,
                         score=score, comment=comment, update_time=update_time)
                for (id_, receiver_id, grader_id, class_id, title, score, comment, update_time) in records]


async def read(grade_id: int) -> do.Grade:
    async with SafeExecutor(
            event='read grade',
            sql=fr'SELECT id, receiver_id, grader_id, class_id, title, score, comment, update_time'
                fr'  FROM grade'
                fr' WHERE id = %(grade_id)s',
            grade_id=grade_id,
            fetch=1,
    ) as (id_, receiver_id, grader_id, class_id, title, score, comment, update_time):
        return do.Grade(id=id_, receiver_id=receiver_id, grader_id=grader_id, class_id=class_id, title=title,
                        score=score, comment=comment, update_time=update_time)


async def edit(grade_id: int, title: Optional[str], score: Optional[int], comment: Optional[str],
               update_time: Optional[datetime] = None) -> None:
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

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update grade by id',
            sql=fr'UPDATE grade'
                fr' WHERE grade.id = %(grade_id)s'
                fr'   SET {set_sql}',
            grade_id=grade_id,
            **to_updates,
    ):
        pass
