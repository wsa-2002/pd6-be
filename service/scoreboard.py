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
    return (scoreboard, scoreboard_setting_data)


async def get_problem_score_under_team(team_id: int, target_problem_ids: Sequence[int]) \
        -> Tuple[Dict[int, vo.ProblemScore], int]:
    """
    Return: Tuple[Dict[problem_id, vo.ProblemScore], total_score]
    """

    team_members = await team.browse_members(team_id=team_id)

    problem_score_team = dict()
    total_score = 0

    for target_problem_id in target_problem_ids:
        problem, submission, judgment = await db.scoreboard_setting_team_project. \
            get_problem_raw_score(problem_id=target_problem_id,
                                  team_member_ids=[team_member.member_id for team_member in team_members])

        total_score += judgment.score
        problem_score_team[problem.id] = vo.ProblemScore(problem_id=problem.id,
                                                         score=judgment.score,
                                                         submission_id=submission.id)
    return problem_score_team, total_score
