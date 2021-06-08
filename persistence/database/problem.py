from typing import Optional, Sequence

from base import do

from .base import SafeExecutor


async def add(title: str, setter_id: int, full_score: int,
              description: Optional[str], source: Optional[str], hint: Optional[str],
              is_hidden: bool, is_deleted: bool) -> int:
    async with SafeExecutor(
            event='Add problem',
            sql="INSERT INTO problem"
                "            (title, setter_id, full_score,"
                "             description, source, hint, is_hidden, is_deleted)"
                "     VALUES (%(title)s, %(setter_id)s, %(full_score)s,"
                "             %(description)s, %(source)s, %(hint)s, %(is_hidden)s, %(is_deleted)s)"
                "  RETURNING id",
            title=title, setter_id=setter_id, full_score=full_score,
            description=description, source=source, hint=hint, is_hidden=is_hidden, is_deleted=is_deleted,
            fetch=1,
    ) as (id_,):
        return id_


async def browse(include_hidden=False, include_deleted=False) -> Sequence[do.Problem]:
    filters = []
    if not include_hidden:
        filters.append("NOT is_hidden")
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(filters)

    async with SafeExecutor(
            event='browse problems',
            sql=fr'SELECT id, title, setter_id, full_score, description, source, hint, is_hidden, is_deleted'
                fr'  FROM problem'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.Problem(id=id_, title=title, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_hidden=is_hidden, is_deleted=is_deleted)
                for id_, title, setter_id, full_score, description, source, hint, is_hidden, is_deleted
                in records]


async def browse_by_challenge(challenge_id: int, include_hidden=False, include_deleted=False) -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problems with challenge id',
            sql=fr'SELECT id, title, setter_id, full_score, description, source, hint, is_hidden, is_deleted'
                fr'  FROM problem'
                fr'       LEFT JOIN challenge_problem'
                fr'              ON problem.id = challenge_problem.problem_id'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY problem_id ASC',
            challenge_id=challenge_id,
            fetch='all',
    ) as records:
        return [do.Problem(id=id_, title=title, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_hidden=is_hidden, is_deleted=is_deleted)
                for id_, title, setter_id, full_score, description, source, hint, is_hidden, is_deleted
                in records]


async def read(problem_id: int, include_hidden=False, include_deleted=False) -> do.Problem:
    async with SafeExecutor(
            event='read problem by id',
            sql=fr'SELECT id, title, setter_id, full_score, description, source, hint, is_hidden, is_deleted'
                fr'  FROM problem'
                fr' WHERE id = %(problem_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            problem_id=problem_id,
            fetch=1,
    ) as (id_, title, setter_id, full_score, description, source, hint, is_hidden, is_deleted):
        return do.Problem(id=id_, title=title, setter_id=setter_id,
                          full_score=full_score, description=description, source=source, hint=hint,
                          is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(problem_id: int,
               title: Optional[str] = None,
               full_score: Optional[int] = None,
               description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,
               is_hidden: Optional[bool] = None,) -> None:
    to_updates = {}

    if title is not None:
        to_updates['title'] = title
    if full_score is not None:
        to_updates['full_score'] = full_score
    if description is not ...:
        to_updates['description'] = description
    if source is not ...:
        to_updates['source'] = source
    if hint is not ...:
        to_updates['hint'] = hint
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit problem',
            sql=fr'UPDATE problem'
                fr'   SET {set_sql}'
                fr' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            **to_updates,
    ):
        pass


async def delete(problem_id: int) -> None:
    async with SafeExecutor(
            event='soft delete problem',
            sql=fr'UPDATE problem'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            is_deleted=True,
    ):
        pass
