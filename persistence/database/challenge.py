from datetime import datetime
from typing import Optional, Sequence, Collection

from base import enum

from . import do
from .base import SafeExecutor


async def add(class_id: int, type_: enum.ChallengeType, name: str, setter_id: int, description: Optional[str],
              start_time: datetime, end_time: datetime, is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='Add challenge',
            sql="INSERT INTO challenge"
                "            (class_id, type, name, setter_id, description,"
                "             start_time, end_time, is_enabled, is_hidden)"
                "     VALUES (%(class_id)s, %(type)s, %(name)s, %(setter_id)s, %(description)s,"
                "             %(start_time)s, %(end_time)s, %(is_enabled)s, %(is_hidden)s)"
                "  RETURNING id",
            class_id=class_id, type=type_, name=name, setter_id=setter_id, description=description,
            start_time=start_time, end_time=end_time, is_enabled=is_enabled, is_hidden=is_hidden,
            fetch=1,
    ) as (id_,):
        return id_


async def browse() -> Sequence[do.Challenge]:
    async with SafeExecutor(
            event='browse challenges',
            sql='SELECT id, class_id, type, name, setter_id, description, start_time, end_time, is_enabled, is_hidden'
                '  FROM challenge',
            fetch='all',
    ) as results:
        return [do.Challenge(id=id_, class_id=class_id, type=type_, name=name, setter_id=setter_id,
                             description=description, start_time=start_time, end_time=end_time,
                             is_enabled=is_enabled, is_hidden=is_hidden)
                for id_, class_id, type_, name, setter_id, description, start_time, end_time, is_enabled, is_hidden
                in results]


async def read(challenge_id: int) -> do.Challenge:
    async with SafeExecutor(
            event='read challenge by id',
            sql='SELECT id, class_id, type, name, setter_id, description, start_time, end_time, is_enabled, is_hidden'
                '  FROM challenge'
                ' WHERE id = %(challenge_id)s',
            challenge_id=challenge_id,
            fetch='all',
    ) as (id_, class_id, type_, name, setter_id, description, start_time, end_time, is_enabled, is_hidden):
        return do.Challenge(id=id_, class_id=class_id, type=type_, name=name, setter_id=setter_id,
                            description=description, start_time=start_time, end_time=end_time,
                            is_enabled=is_enabled, is_hidden=is_hidden)


async def edit(challenge_id: int,
               type_: Optional[enum.ChallengeType] = None,
               name: Optional[str] = None,
               description: Optional[str] = ...,
               start_time: Optional[datetime] = None,
               end_time: Optional[datetime] = None,
               is_enabled: Optional[bool] = None,
               is_hidden: Optional[bool] = None) -> None:
    to_updates = {}

    if type_ is not None:
        to_updates['type'] = type_
    if name is not None:
        to_updates['name'] = name
    if description is not ...:
        to_updates['description'] = description
    if start_time is not None:
        to_updates['start_time'] = start_time
    if end_time is not None:
        to_updates['end_time'] = end_time
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    if set_sql:
        async with SafeExecutor(
                event='edit challenge',
                sql=fr'UPDATE challenge'
                    fr' WHERE id = challenge_id'
                    fr'   SET {set_sql}',
                challenge_id=challenge_id,
                **to_updates,
        ):
            pass


async def add_problem_relation(challenge_id: int, problem_id: int) -> None:
    async with SafeExecutor(
            event='delete challenge_problem',
            sql='INSERT INTO challenge_problem'
                '            (challenge_id, problem_id)'
                '     VALUES (%(challenge_id)s, %(problem_id)s)',
            challenge_id=challenge_id,
            problem_id=problem_id,
    ):
        pass


async def browse_problems(challenge_id: int) -> Collection[int]:
    async with SafeExecutor(
            event='browse problems with challenge id',
            sql='SELECT problem_id'
                '  FROM challenge_problem'
                ' WHERE challenge_id = %(challenge_id)s',
            challenge_id=challenge_id,
            fetch='all',
    ) as results:
        return [problem_id for (problem_id,) in results]


async def delete_problem_relation(challenge_id: int, problem_id: int) -> None:
    async with SafeExecutor(
            event='delete challenge_problem',
            sql='DELETE FROM challenge_problem'
                '      WHERE challenge_id = %(challenge_id)s'
                '        AND problem_id = %(problem_id)s',
            challenge_id=challenge_id,
            problem_id=problem_id,
    ):
        pass
