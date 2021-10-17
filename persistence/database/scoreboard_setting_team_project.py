from typing import Sequence, Optional

from base import do, enum

from .base import SafeExecutor


async def add(scoring_formula: str, baseline_team_id: Optional[int],
              rank_by_total_score: bool, team_label_filter: Optional[str]) -> int:
    async with SafeExecutor(
            event='Add scoreboard_setting_team_project',
            sql="INSERT INTO scoreboard_setting_team_project"
                "            (scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter)"
                "     VALUES (%(scoring_formula)s, %(baseline_team_id)s, %(rank_by_total_score)s, %(team_label_filter)s)"
                "  RETURNING id",
            scoring_formula=scoring_formula, baseline_team_id=baseline_team_id,
            rank_by_total_score=rank_by_total_score, team_label_filter=team_label_filter,
            fetch=1,
    ) as (id_,):
        return id_
