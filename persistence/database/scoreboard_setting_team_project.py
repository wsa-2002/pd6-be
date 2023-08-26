from typing import Sequence, Optional

import asyncpg

from base import do, enum
import exceptions as exc

from . import scoreboard
from .base import AutoTxConnection, OnlyExecute, FetchOne, ParamDict


async def add_under_scoreboard(challenge_id: int, challenge_label: str, title: str, target_problem_ids: Sequence[int],
                               type_: enum.ScoreboardType, scoring_formula: str, baseline_team_id: Optional[int],
                               rank_by_total_score: bool, team_label_filter: Optional[str]) -> int:
    async with AutoTxConnection(event='add scoreboard_setting_team_project under scoreboard') as conn:
        try:
            (team_project_scoreboard_id,) = await conn.fetchrow(
                "INSERT INTO scoreboard_setting_team_project"
                "            (scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter)"
                "     VALUES ($1, $2, $3, $4)"
                "  RETURNING id",
                scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter,
            )

            (scoreboard_id,) = await conn.fetchrow(
                "INSERT INTO scoreboard"
                "            (challenge_id, challenge_label, title, target_problem_ids, type, setting_id)"
                "     VALUES ($1, $2, $3, $4, $5, $6) "
                "  RETURNING id",
                challenge_id, challenge_label, title, target_problem_ids, type_, team_project_scoreboard_id,
            )

            return scoreboard_id
        except asyncpg.exceptions.ForeignKeyViolationError:
            raise exc.IllegalInput


async def read(scoreboard_setting_team_project_id: int) -> do.ScoreboardSettingTeamProject:
    async with FetchOne(
            event='read scoreboard_setting_team_project',
            sql=r'SELECT id, scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter'
                r'  FROM scoreboard_setting_team_project'
                r' WHERE id = %(scoreboard_setting_team_project_id)s',
            scoreboard_setting_team_project_id=scoreboard_setting_team_project_id,
    ) as (id_, scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter):
        return do.ScoreboardSettingTeamProject(
            id=id_, scoring_formula=scoring_formula, baseline_team_id=baseline_team_id,
            rank_by_total_score=rank_by_total_score, team_label_filter=team_label_filter,
        )


async def edit_with_scoreboard(scoreboard_id: int,
                               challenge_label: str = None,
                               title: str = None,
                               target_problem_ids: Sequence[int] = None,
                               scoring_formula: str = None,
                               baseline_team_id: Optional[int] = ...,
                               rank_by_total_score: bool = None,
                               team_label_filter: Optional[str] = ...) -> None:
    scoreboard_to_updates: ParamDict = {}

    if challenge_label is not None:
        scoreboard_to_updates['challenge_label'] = challenge_label
    if title is not None:
        scoreboard_to_updates['title'] = title
    if target_problem_ids is not None:
        scoreboard_to_updates['target_problem_ids'] = target_problem_ids

    scoreboard_setting_to_updates: ParamDict = {}

    if scoring_formula is not None:
        scoreboard_setting_to_updates['scoring_formula'] = scoring_formula
    if baseline_team_id is not ...:
        scoreboard_setting_to_updates['baseline_team_id'] = baseline_team_id
    if rank_by_total_score is not None:
        scoreboard_setting_to_updates['rank_by_total_score'] = rank_by_total_score
    if team_label_filter is not ...:
        scoreboard_setting_to_updates['team_label_filter'] = team_label_filter

    if scoreboard_to_updates:
        set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in scoreboard_to_updates)

        async with OnlyExecute(
                event='edit scoreboard',
                sql=fr'UPDATE scoreboard'
                    fr'   SET {set_sql}'
                    fr' WHERE id = %(scoreboard_id)s',
                scoreboard_id=scoreboard_id,
                **scoreboard_to_updates,
        ):
            pass

    if scoreboard_setting_to_updates:
        scoreboard_ = await scoreboard.read(scoreboard_id=scoreboard_id)
        set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in scoreboard_setting_to_updates)

        async with OnlyExecute(
                event='edit scoreboard_setting_team_project',
                sql=fr'UPDATE scoreboard_setting_team_project'
                    fr'   SET {set_sql}'
                    fr' WHERE id = %(scoreboard_setting_team_project_id)s',
                scoreboard_setting_team_project_id=scoreboard_.setting_id,
                **scoreboard_setting_to_updates,
        ):
            pass
