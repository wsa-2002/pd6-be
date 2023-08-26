from typing import Sequence

from base import do
from base.enum import ScoreboardType

from .base import OnlyExecute, FetchOne, FetchAll


async def browse_by_challenge(challenge_id: int, include_deleted=False) -> Sequence[do.Scoreboard]:
    async with FetchAll(
            event='browse scoreboards with challenge id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, target_problem_ids, is_deleted, type, setting_id'
                fr'  FROM scoreboard'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            challenge_id=challenge_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Scoreboard(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                              target_problem_ids=target_problem_ids, is_deleted=is_deleted, type=type_, setting_id=setting_id)
                for (id_, challenge_id, challenge_label, title, target_problem_ids, is_deleted, type_, setting_id) in records]


async def read(scoreboard_id: int, *, include_deleted=False) -> do.Scoreboard:
    async with FetchOne(
            event='read scoreboard',
            sql=fr'SELECT id, challenge_id, challenge_label, title, target_problem_ids, is_deleted, type, setting_id'
                fr'  FROM scoreboard'
                fr' WHERE id = %(scoreboard_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            scoreboard_id=scoreboard_id,
    ) as (id_, challenge_id, challenge_label, title, target_problem_ids, is_deleted, type_, setting_id):
        return do.Scoreboard(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                             target_problem_ids=target_problem_ids, is_deleted=is_deleted,
                             type=ScoreboardType(type_), setting_id=setting_id)


async def delete(scoreboard_id: int) -> None:
    async with OnlyExecute(
            event='soft delete scoreboard',
            sql=r'UPDATE scoreboard'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(scoreboard_id)s',
            is_deleted=True,
            scoreboard_id=scoreboard_id,
    ):
        return
