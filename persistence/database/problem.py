from typing import Optional, Sequence

from base import do, enum

from .base import SafeExecutor


async def add(title: str, setter_id: int, full_score: int,
              description: Optional[str], source: Optional[str], hint: Optional[str],
              is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='Add problem',
            sql="INSERT INTO problem"
                "            (title, setter_id, full_score,"
                "             description, source, hint, is_enabled, is_hidden)"
                "     VALUES (%(title)s, %(setter_id)s, %(full_score)s,"
                "             %(description)s, %(source)s, %(hint)s, %(is_enabled)s, %(is_hidden)s)"
                "  RETURNING id",
            title=title, setter_id=setter_id, full_score=full_score,
            description=description, source=source, hint=hint, is_enabled=is_enabled, is_hidden=is_hidden,
            fetch=1,
    ) as (id_,):
        return id_


async def browse() -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problems',
            sql='SELECT id, title, setter_id, full_score, description, source, hint, is_enabled, is_hidden'
                '  FROM problem'
                ' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.Problem(id=id_, title=title, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_enabled=is_enabled, is_hidden=is_hidden)
                for id_, title, setter_id, full_score, description, source, hint, is_enabled, is_hidden
                in records]


async def browse_by_challenge(challenge_id: int) -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problems with challenge id',
            sql='SELECT id, title, setter_id, full_score, description, source, hint, is_enabled, is_hidden'
                '  FROM problem'
                '       LEFT JOIN challenge_problem'
                '              ON problem.id = challenge_problem.problem_id'
                ' WHERE challenge_id = %(challenge_id)s'
                ' ORDER BY problem_id ASC',
            challenge_id=challenge_id,
            fetch='all',
    ) as records:
        return [do.Problem(id=id_, title=title, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_enabled=is_enabled, is_hidden=is_hidden)
                for id_, title, setter_id, full_score, description, source, hint, is_enabled, is_hidden
                in records]


async def read(problem_id: int) -> do.Problem:
    async with SafeExecutor(
            event='read problem by id',
            sql='SELECT id, title, setter_id, full_score, description, source, hint, is_enabled, is_hidden'
                '  FROM problem'
                ' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            fetch=1,
    ) as (id_, title, setter_id, full_score, description, source, hint, is_enabled, is_hidden):
        return do.Problem(id=id_, title=title, setter_id=setter_id,
                          full_score=full_score, description=description, source=source, hint=hint,
                          is_enabled=is_enabled, is_hidden=is_hidden)


async def edit(problem_id: int,
               title: Optional[str] = None,
               full_score: Optional[int] = None,
               description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,
               is_enabled: Optional[bool] = None,
               is_hidden: Optional[bool] = None) -> None:
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
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit problem',
            sql=fr'UPDATE problem'
                fr' WHERE id = %(problem_id)s'
                fr'   SET {set_sql}',
            problem_id=problem_id,
            **to_updates,
    ):
        pass


async def delete(problem_id: int) -> None:
    ...  # TODO
