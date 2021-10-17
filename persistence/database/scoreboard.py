from dataclasses import dataclass
from typing import Sequence, Tuple, Any, Optional

from base import do
from base.enum import ScoreboardType

from . import scoreboard_setting_team_project
from .base import SafeExecutor, SafeConnection


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


async def read(scoreboard_id: int, include_deleted=False) -> do.Scoreboard:
    async with SafeExecutor(
            event='read scoreboard',
            sql=fr'SELECT id, challenge_id, label, title, target_problem_ids, is_deleted, type, setting_id'
                fr'  FROM scoreboard'
                fr' WHERE id = %(scoreboard_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            scoreboard_id=scoreboard_id,
            fetch=1,
    ) as (id_, challenge_id, label, title, target_problem_ids, is_deleted, type, setting_id):
        return do.Scoreboard(id=id_, challenge_id=challenge_id, label=label, title=title,
                             target_problem_ids=target_problem_ids, is_deleted=is_deleted,
                             type=ScoreboardType(type), setting_id=setting_id)


@dataclass
class ScoreboardSettingTeamProjectDataOutput:
    scoring_formula: str
    baseline_team_id: Optional[int]
    rank_by_total_score: bool
    team_label_filter: Optional[str]


async def read_with_scoreboard_setting_data(scoreboard_id: int, include_deleted=False) -> Tuple[do.Scoreboard, Any]:
    async with SafeConnection(event=f'read scoreboard with scoreboard setting data') as conn:
        async with conn.transaction():

            scoreboard = await read(scoreboard_id=scoreboard_id)

            if scoreboard.type is ScoreboardType.team_project:
                result = await scoreboard_setting_team_project.read(
                    scoreboard_setting_team_project_id=scoreboard.setting_id
                )
                scoreboard_setting_data = ScoreboardSettingTeamProjectDataOutput(scoring_formula=result.scoring_formula,
                                                                                 baseline_team_id=result.baseline_team_id,
                                                                                 rank_by_total_score=result.rank_by_total_score,
                                                                                 team_label_filter=result.team_label_filter)

            return (scoreboard, scoreboard_setting_data)
