from typing import Optional, Sequence

from base import do, enum

from .base import SafeExecutor


async def add(challenge_id: int, identifier: str, selection_type: enum.TaskSelectionType,
              problem_id: Optional[int], peer_review_id: Optional[int]) -> int:
    async with SafeExecutor(
            event='Add task',
            sql="INSERT INTO task"
                "            (challenge_id, identifier, selection_type,"
                "             problem_id, peer_review_id)"
                "     VALUES (%(challenge_id)s, %(identifier)s, %(selection_type)s,"
                "             %(problem_id)s, %(peer_review_id)s)"
                "  RETURNING id",
            challenge_id=challenge_id, identifier=identifier, selection_type=selection_type,
            problem_id=problem_id, peer_review_id=peer_review_id,
            fetch=1,
    ) as (id_,):
        return id_


async def browse(challenge_id: int) -> Sequence[do.Task]:
    async with SafeExecutor(
            event='browse tasks',
            sql='SELECT id, challenge_id, identifier, selection_type,'
                '       problem_id, peer_review_id'
                '  FROM task'
                ' WHERE challenge_id = %(challenge_id)s'
                ' ORDER BY identifier ASC',
            challenge_id=challenge_id,
            fetch='all',
    ) as records:
        return [do.Task(id=id_, challenge_id=challenge_id, identifier=identifier, selection_type=selection_type,
                        problem_id=problem_id, peer_review_id=peer_review_id)
                for (id_, challenge_id, identifier, selection_type,
                     problem_id, peer_review_id)
                in records]


async def read(task_id: int) -> do.Task:
    async with SafeExecutor(
            event='browse tasks',
            sql='SELECT id, challenge_id, identifier, selection_type,'
                '       problem_id, peer_review_id'
                '  FROM task'
                ' WHERE id = %(task_id)s'
                ' ORDER BY identifier ASC',
            task_id=task_id,
            fetch='all',
    ) as (id_, challenge_id, identifier, selection_type,
          problem_id, peer_review_id):
        return do.Task(id=id_, challenge_id=challenge_id, identifier=identifier, selection_type=selection_type,
                       problem_id=problem_id, peer_review_id=peer_review_id)


async def delete(task_id: int) -> None:
    async with SafeExecutor(
            event='delete task',
            sql='DELETE FROM task'
                ' WHERE id = %(task_id)s',
            task_id=task_id,
    ):
        pass
