from typing import Optional, Sequence

from base import do, enum

from .base import SafeExecutor


async def add(challenge_id: int, identifier: str, selection_type: enum.TaskSelectionType,
              problem_id: Optional[int], peer_review_id: Optional[int], is_hidden: bool) -> int:
    async with SafeExecutor(
            event='Add task',
            sql="INSERT INTO task"
                "            (challenge_id, identifier, selection_type,"
                "             problem_id, peer_review_id, is_hidden)"
                "     VALUES (%(challenge_id)s, %(identifier)s, %(selection_type)s,"
                "             %(problem_id)s, %(peer_review_id)s, %(is_hidden)s)"
                "  RETURNING id",
            challenge_id=challenge_id, identifier=identifier, selection_type=selection_type,
            problem_id=problem_id, peer_review_id=peer_review_id, is_hidden=is_hidden,
            fetch=1,
    ) as (id_,):
        return id_


async def browse(challenge_id: int, include_hidden=False, include_deleted=False) -> Sequence[do.Task]:
    async with SafeExecutor(
            event='browse tasks',
            sql=fr'SELECT id, challenge_id, identifier, selection_type,'
                fr'       problem_id, peer_review_id, is_hidden, is_deleted'
                fr'  FROM task'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY identifier ASC',
            challenge_id=challenge_id,
            fetch='all',
    ) as records:
        return [do.Task(id=id_, challenge_id=challenge_id, identifier=identifier,
                        selection_type=enum.TaskSelectionType(selection_type),
                        problem_id=problem_id, peer_review_id=peer_review_id,
                        is_hidden=is_hidden, is_deleted=is_deleted)
                for (id_, challenge_id, identifier, selection_type,
                     problem_id, peer_review_id, is_hidden, is_deleted)
                in records]


async def read(task_id: int, include_hidden=False, include_deleted=False) -> do.Task:
    async with SafeExecutor(
            event='browse tasks',
            sql=fr'SELECT id, challenge_id, identifier, selection_type,'
                fr'       problem_id, peer_review_id, is_hidden, is_deleted'
                fr'  FROM task'
                fr' WHERE id = %(task_id)s'
                fr'{" AND NOT is_hidden" if not include_hidden else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY identifier ASC',
            task_id=task_id,
            fetch='all',
    ) as (id_, challenge_id, identifier, selection_type,
          problem_id, peer_review_id, is_hidden, is_deleted):
        return do.Task(id=id_, challenge_id=challenge_id, identifier=identifier,
                       selection_type=enum.TaskSelectionType(selection_type),
                       problem_id=problem_id, peer_review_id=peer_review_id,
                       is_hidden=is_hidden, is_deleted=is_deleted)


async def edit(task_id: int,
               identifier: str = None, selection_type: enum.TaskSelectionType = None, is_hidden: bool = None,
               problem_id: Optional[int] = None, peer_review_id: Optional[int] = None) -> None:
    if problem_id is not None and peer_review_id is not None:
        raise ValueError("Only one id can be given to a task")

    to_updates = {}

    if identifier is not None:
        to_updates['identifier'] = identifier
    if selection_type is not None:
        to_updates['selection_type'] = selection_type
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden
    if problem_id is not None or peer_review_id is not None:
        to_updates['problem_id'] = problem_id
        to_updates['peer_review_id'] = peer_review_id

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='update task by id',
            sql=fr'UPDATE task'
                fr'   SET {set_sql}'
                fr' WHERE id = %(task_id)s',
            task_id=task_id,
            **to_updates,
    ):
        pass


async def delete(task_id: int) -> None:
    async with SafeExecutor(
            event='soft delete task',
            sql=fr'UPDATE task'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(task_id)s',
            task_id=task_id,
            is_deleted=True,
    ):
        pass
