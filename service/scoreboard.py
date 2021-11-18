from typing import Tuple, Optional, Any, Sequence
from dataclasses import dataclass

import asyncpg

from base import do, enum, vo
import exceptions as exc
import persistence.database as db


FORMULA_AVAILABLE_PARAMS = ['class_best', 'class_worst', 'baseline', 'team_score']


# TODO: More Validation
async def validate_formula(formula: str) -> bool:

    for param in FORMULA_AVAILABLE_PARAMS:
        formula = formula.replace(param, '')

    return not any(char.isalpha() for char in formula)


@dataclass
class ScoreboardSettingTeamProjectData:
    scoring_formula: str
    baseline_team_id: Optional[int]
    rank_by_total_score: bool
    team_label_filter: Optional[str]


async def read_with_scoreboard_setting_data(scoreboard_id: int) -> Tuple[do.Scoreboard, Any]:
    scoreboard = await db.scoreboard.read(scoreboard_id=scoreboard_id)
    scoreboard_setting_data = None

    if scoreboard.type is enum.ScoreboardType.team_project:
        result = await db.scoreboard_setting_team_project.read(scoreboard_setting_team_project_id=scoreboard.setting_id)
        scoreboard_setting_data = ScoreboardSettingTeamProjectData(scoring_formula=result.scoring_formula,
                                                                   baseline_team_id=result.baseline_team_id,
                                                                   rank_by_total_score=result.rank_by_total_score,
                                                                   team_label_filter=result.team_label_filter)
    return scoreboard, scoreboard_setting_data


async def _team_project_calculate_score(team_raw_score: dict[int, int], formula: str,
                                        baseline_team_id: int = None) -> dict[int, int]:
    """
    Return: dict[team_id, score]
    """
    params = dict()

    params['class_best'] = max(team_raw_score.values())
    params['class_worst'] = min(team_raw_score.values())
    if baseline_team_id is not None:
        try:
            params['baseline'] = team_raw_score[baseline_team_id]
        except KeyError:
            params['baseline'] = 0  # baseline team have not submitted

    team_score_dict = dict()
    for team_id in team_raw_score:
        params['team_score'] = team_raw_score[team_id]

        try:
            team_score_dict[team_id] = eval(formula, params)
        except ZeroDivisionError:
            team_score_dict[team_id] = 0  # if divided by zero in formula, team score will be 0
        except (TypeError, NameError, SyntaxError):
            raise exc.InvalidFormula

    return team_score_dict


async def view_team_project_scoreboard(scoreboard_id: int) -> Sequence[vo.ViewTeamProjectScoreboard]:
    scoreboard, scoreboard_setting_data = await read_with_scoreboard_setting_data(scoreboard_id)
    challenge = await db.challenge.read(challenge_id=scoreboard.challenge_id, include_scheduled=True)
    try:
        teams = await db.team.browse_with_team_label_filter(class_id=challenge.class_id,
                                                            team_label_filter=scoreboard_setting_data.team_label_filter)
    except asyncpg.InvalidRegularExpressionError:
        raise exc.InvalidTeamLabelFilter

    team_data = {team.id: [] for team in teams}

    for target_problem_id in scoreboard.target_problem_ids:
        team_submission, team_judgment = await db.judgment.get_class_last_team_submission_judgment(
            problem_id=target_problem_id, class_id=challenge.class_id, team_ids=[team.id for team in teams])

        testcases = await db.testcase.browse(problem_id=target_problem_id)
        team_score_problem = {team.id: 0 for team in teams}
        for testcase in testcases:
            judge_cases = await db.judge_case.batch_get_with_judgment(
                testcase_id=testcase.id, judgment_ids=[judgment_id for team_id, judgment_id in team_judgment.items()])

            team_raw_score = {
                team_id: judge_cases[judgment_id].score
                if judgment_id in judge_cases.keys() else 0  # Judgment without judge_case: judge_case.score will be 0
                for team_id, judgment_id in team_judgment.items()
            }

            team_calculated_score = await _team_project_calculate_score(
                team_raw_score=team_raw_score,
                formula=scoreboard_setting_data.scoring_formula,
                baseline_team_id=scoreboard_setting_data.baseline_team_id
            )

            for team_id in team_calculated_score:
                team_score_problem[team_id] += team_calculated_score[team_id]

        for team_id in team_submission:
            team_data[team_id].append(vo.ProblemScore(problem_id=target_problem_id,
                                                      score=team_score_problem[team_id],
                                                      submission_id=team_submission[team_id]))

    return [vo.ViewTeamProjectScoreboard(team_id=team.id,
                                         team_name=team.name,
                                         total_score=sum([problem_score.score for problem_score in team_data[team.id]]),
                                         target_problem_data=[problem_score for problem_score in team_data[team.id]])
            for team in teams]
