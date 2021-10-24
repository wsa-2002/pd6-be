from typing import Sequence, Tuple

import service.scoreboard
from base import do, vo
import persistence.database as db


add_under_scoreboard = db.scoreboard_setting_team_project.add_under_scoreboard
edit_with_scoreboard = db.scoreboard_setting_team_project.edit_with_scoreboard


TEAM_SCORE_FORMULA_PARAMS = {
    'team_score': int,
    'class_best': int,
    'class_worst': int,
    'baseline': int,
}

# TODO: dict params
async def calculate_score(formula: str,
                          team_score: int, class_best: int, class_worst: int, baseline: int) -> int:

    TEAM_SCORE_FORMULA_PARAMS['team_score'] = team_score
    TEAM_SCORE_FORMULA_PARAMS['class_best'] = class_best
    TEAM_SCORE_FORMULA_PARAMS['class_worst'] = class_worst
    TEAM_SCORE_FORMULA_PARAMS['baseline'] = baseline

    return eval(formula, TEAM_SCORE_FORMULA_PARAMS)


async def view_team_scoreboard(scoreboard_id: int) -> Sequence[vo.ViewTeamProjectScoreboard]:

    scoreboard, scoreboard_setting_data = await service.scoreboard.read_with_scoreboard_setting_data(scoreboard_id=scoreboard_id)
    teams = await db.team.browse_with_team_label_filter(team_label_filter=scoreboard_setting_data.team_label_filter)


    for target_problem_id in scoreboard.target_problem_ids:
        data = await service.judgment.get_class_last_team_submission_judgment(problem_id=target_problem_id,
                                                                              class_id=team.class_id,
                                                                              team_ids=[team.id for team in teams])

        problem_score = 0
        testcases = await db.testcase.browse(problem_id=target_problem_id)
        for testcase in testcases:
            judge_cases = await db.judge_case.batch_get_with_judgment(
                testcase_id=testcase.id,
                judgment_ids=[judgment.id for (team, submission, judgment) in data])
            score = [judge_case.score for judge_case in judge_cases]



