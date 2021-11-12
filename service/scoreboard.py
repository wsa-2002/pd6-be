from typing import Sequence, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from . import team
from base import vo, do, enum
import persistence.database as db


read = db.scoreboard.read
delete = db.scoreboard.delete


@dataclass
class ScoreboardSettingTeamProjectData:
    scoring_formula: str
    baseline_team_id: Optional[int]
    rank_by_total_score: bool
    team_label_filter: Optional[str]


async def read_with_scoreboard_setting_data(scoreboard_id: int) -> Tuple[do.Scoreboard, Any]:
    scoreboard = await db.scoreboard.read(scoreboard_id=scoreboard_id)

    if scoreboard.type is enum.ScoreboardType.team_project:
        result = await db.scoreboard_setting_team_project.read(scoreboard_setting_team_project_id=scoreboard.setting_id)
        scoreboard_setting_data = ScoreboardSettingTeamProjectData(scoring_formula=result.scoring_formula,
                                                                   baseline_team_id=result.baseline_team_id,
                                                                   rank_by_total_score=result.rank_by_total_score,
                                                                   team_label_filter=result.team_label_filter)
    return scoreboard, scoreboard_setting_data
