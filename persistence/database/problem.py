from typing import Optional, Sequence
from datetime import datetime

import log
from base import do, enum

from .base import SafeExecutor


async def add(challenge_id: int, challenge_label: str, selection_type: enum.TaskSelectionType,
              title: str, setter_id: int, full_score: int, description: Optional[str],
              source: Optional[str], hint: Optional[str], is_hidden: bool) -> int:
    async with SafeExecutor(
            event='Add problem',
            sql="INSERT INTO problem"
                "            (challenge_id, challenge_label, selection_type,"
                "             title, setter_id, full_score, description,"
                "             source, hint, is_hidden)"
                "     VALUES (%(title)s, %(setter_id)s, %(full_score)s, %(description)s,"
                "             %(source)s, %(hint)s, %(is_hidden)s)"
                "  RETURNING id",
            challenge_id=challenge_id, challenge_label=challenge_label, selection_type=selection_type,
            title=title, setter_id=setter_id, full_score=full_score, description=description,
            source=source, hint=hint, is_hidden=is_hidden,
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
            sql=fr'SELECT id, challenge_id, challenge_label, selection_type, title, setter_id, full_score, '
                fr'       description, source, hint, is_hidden, is_deleted'
                fr'  FROM problem'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           selection_type=enum.TaskSelectionType(selection_type),
                           title=title, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, selection_type, title, setter_id, full_score,
                     description, source, hint, is_hidden, is_deleted)
                in records]


async def browse_problem_set(request_time: datetime, include_hidden=False, include_deleted=False) \
        -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problem set',
            sql=fr'SELECT problem.id, problem.challenge_id, problem.challenge_label, problem.selection_type, '
                fr'       problem.title, problem.setter_id, problem.full_score, problem.description, '
                fr'       problem.source, problem.hint, problem.is_hidden, problem.is_deleted'
                fr'  FROM problem'
                fr'       INNER JOIN challenge'
                fr'               ON challenge.id = problem.challenge_id'
                fr' WHERE challenge.publicize_type = %(start_time)s AND challenge.start_time <= %(request_time)s'
                fr'    OR challenge.publicize_type = %(end_time)s AND challenge.end_time <= %(request_time)s'
                fr'{" AND NOT problem.is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT problem.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY problem.id ASC',
            request_time=request_time,
            start_time=enum.ChallengePublicizeType.start_time,
            end_time=enum.ChallengePublicizeType.end_time,
            fetch='all',
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           selection_type=enum.TaskSelectionType(selection_type),
                           title=title, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, selection_type, title, setter_id, full_score,
                     description, source, hint, is_hidden, is_deleted)
                in records]


async def browse_by_challenge(challenge_id: int, include_hidden=False, include_deleted=False) -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problems with challenge id',
            sql=fr'SELECT id, challenge_id, challenge_label, selection_type, title, setter_id, full_score, '
                fr'       description, source, hint, is_hidden, is_deleted'
                fr'  FROM problem'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            challenge_id=challenge_id,
            fetch='all',
    ) as records:
        return [do.Problem(id=id_,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           selection_type=enum.TaskSelectionType(selection_type),
                           title=title, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, selection_type, title, setter_id, full_score,
                     description, source, hint, is_hidden, is_deleted)
                in records]


async def read(problem_id: int, include_hidden=False, include_deleted=False) -> do.Problem:
    async with SafeExecutor(
            event='read problem by id',
            sql=fr'SELECT id, challenge_id, challenge_label, selection_type, title, setter_id, full_score, '
                fr'       description, source, hint, is_hidden, is_deleted'
                fr'  FROM problem'
                fr' WHERE id = %(problem_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            problem_id=problem_id,
            fetch=1,
    ) as (id_, challenge_id, challenge_label, selection_type, title, setter_id, full_score,
          description, source, hint, is_hidden, is_deleted):
        return do.Problem(id=id_,
                          challenge_id=challenge_id, challenge_label=challenge_label,
                          selection_type=enum.TaskSelectionType(selection_type),
                          title=title, setter_id=setter_id,
                          full_score=full_score, description=description, source=source, hint=hint,
                          is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(problem_id: int,
               challenge_label: str = None,
               selection_type: enum.TaskSelectionType = None,
               title: str = None,
               full_score: int = None,
               description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,
               is_hidden: bool = None,) -> None:
    to_updates = {}

    if challenge_label is not None:
        to_updates['challenge_label'] = challenge_label
    if selection_type is not None:
        to_updates['selection_type'] = selection_type
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
