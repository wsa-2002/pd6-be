from typing import Sequence

from base import do, enum

from .base import SafeExecutor


async def add(challenge_id: int, label: str, title: str, target_problem_ids: Sequence[int],
              type: enum.ScoreboardType, setting_id: int) -> int:
    async with SafeExecutor(
            event='Add scoreboard',
            sql="INSERT INTO scoreboard"
                "            (challenge_id, label, title, target_problem_ids, type, setting_id)"
                "     VALUES (%(challenge_id)s, %(label)s, %(title)s, %(target_problem_ids)s, "
                "             %(type)s, %(setting_id)s)"
                "  RETURNING id",
            challenge_id=challenge_id, label=label, title=title,
            target_problem_ids=target_problem_ids, type=type, setting_id=setting_id,
            fetch=1,
    ) as (id_,):
        return id_


async def browse_by_challenge(challenge_id: int, include_deleted=False) -> Sequence[do.Scoreboard]:
    async with SafeExecutor(
            event='browse scoreboards with challenge id',
            sql=fr'SELECT id, challenge_id, label, title, target_problem_ids, is_deleted, type, setting_id'
                fr'  FROM scoreboard'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            challenge_id=challenge_id,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Scoreboard(id=id_, challenge_id=challenge_id, label=label, title=title,
                              target_problem_ids=target_problem_ids, is_deleted=is_deleted, type=type, setting_id=setting_id)
                for (id_, challenge_id, label, title, target_problem_ids, is_deleted, type, setting_id) in records]
