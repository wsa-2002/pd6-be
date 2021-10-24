from typing import Sequence, Dict

from . import scoreboard, problem
from base import vo
import persistence.database as db


add_under_scoreboard = db.scoreboard_setting_team_project.add_under_scoreboard
edit_with_scoreboard = db.scoreboard_setting_team_project.edit_with_scoreboard


TEAM_SCORE_FORMULA_PARAMS = {
    'team_score': int,
    'class_best': int,
    'class_worst': int,
    'baseline': int,
}


async def calculate_score(formula: str,
                          team_score: int, class_best: int, class_worst: int, baseline: int) -> int:

    TEAM_SCORE_FORMULA_PARAMS['team_score'] = team_score
    TEAM_SCORE_FORMULA_PARAMS['class_best'] = class_best
    TEAM_SCORE_FORMULA_PARAMS['class_worst'] = class_worst
    TEAM_SCORE_FORMULA_PARAMS['baseline'] = baseline

    return eval(formula, TEAM_SCORE_FORMULA_PARAMS)


async def get_problem_raw_score(class_id: int, team_label_filter: str,
                                   target_problem_ids: Sequence[int], rank_by_total_score: bool)\
        -> Dict[int, vo.TeamProjectRawScoreboard]:

    scoreboard_setting_team_projects = dict()

    teams = await db.team.browse_with_team_label_filter(team_label_filter=team_label_filter, class_id=class_id)
    for team in teams:
        problem_score_team, total_score = await scoreboard.get_problem_score_under_team(
            team_id=team.id,
            target_problem_ids=[problem_id for problem_id in target_problem_ids]
        )

        scoreboard_setting_team_projects[team.id] = vo.TeamProjectRawScoreboard(
            team_id=team.id,
            team_name=team.name,
            total_score=total_score if rank_by_total_score else None,
            target_problem_raw_data=problem_score_team
        )

    return scoreboard_setting_team_projects


async def get_problem_customized_score(scoreboard_setting_team_projects, target_problem_ids: Sequence[int],
                                       scoring_formula: str, rank_by_total_score: bool, baseline_team_id: int = None)\
        -> Dict[int, vo.TeamProjectRawScoreboard]:
    """
    Return: Dict[team_id, vo.TeamProjectRawScoreboard]
    """

    # find baseline team
    if baseline_team_id is not None:
        baseline_team = scoreboard_setting_team_projects[baseline_team_id]

    # to find class best / worst
    problem_scores = dict()  # key: problem_id, value: scores[]
    for target_problem_id in target_problem_ids:  # 每題
        problem_scores[target_problem_id] = []
        for team_id, scoreboard_setting_team_project in scoreboard_setting_team_projects.items():  # 每組
            problem_scores[target_problem_id].append(
                scoreboard_setting_team_project.target_problem_raw_data[target_problem_id].score)



    new_scoreboards = dict()


    for team_id, scoreboard_setting_team_project in scoreboard_setting_team_projects.items():  # for each team
        team_score = scoreboard_setting_team_project.target_problem_raw_data[target_problem_id].score

        new_problem_datas = dict()
        for target_problem_id in target_problem_ids:
            target_problem = await problem.read(problem_id=target_problem_id)  # TODO: add problem_judge_type

            class_best = max(problem_scores[target_problem_id])
            class_worst = min(problem_scores[target_problem_id])
            baseline = baseline_team.target_problem_raw_data[target_problem_id].score

            calculated_score = await calculate_score(formula=scoring_formula, team_score=team_score,
                                                     class_best=class_best, class_worst=class_worst, baseline=baseline)

            new_problem_datas[target_problem_id] = vo.ProblemScore(
                problem_id=target_problem_id,
                score=calculated_score if target_problem.judge_type is ProblemJudgeType.customized
                    else scoreboard_setting_team_project.target_problem_raw_data[target_problem_id].score,
                submission_id=scoreboard_setting_team_project.target_problem_raw_data[target_problem_id].submission_id
            )

        new_scoreboards[team_id] = vo.TeamProjectRawScoreboard(
            team_id=scoreboard_setting_team_project.team_id,
            team_name=scoreboard_setting_team_project.team_name,
            total_score=scoreboard_setting_team_project.total_score if rank_by_total_score else None,
            target_problem_raw_data=new_problem_datas
        )

    return new_scoreboards
