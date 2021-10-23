from typing import Sequence, Dict, Tuple

from . import team
from base import vo
import persistence.database as db


read = db.scoreboard.read
read_with_scoreboard_setting_data = db.scoreboard.read_with_scoreboard_setting_data
delete = db.scoreboard.delete


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
