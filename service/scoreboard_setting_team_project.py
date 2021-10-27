from typing import Sequence, Tuple, Optional

import service.scoreboard
from base import do, vo, enum
import persistence.database as db
import exceptions as exc


edit_with_scoreboard = db.scoreboard_setting_team_project.edit_with_scoreboard


async def add_under_scoreboard(challenge_id: int, challenge_label: str, title: str, target_problem_ids: Sequence[int],
                               type: enum.ScoreboardType, scoring_formula: str, baseline_team_id: Optional[int],
                               rank_by_total_score: bool, team_label_filter: Optional[str]) -> int:

    # Exception Handling
    scoreboard_challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True)

    if baseline_team_id is not None:
        baseline_team = await db.team.read(team_id=baseline_team_id, include_deleted=True)
        if baseline_team.class_id is not scoreboard_challenge.class_id:
            raise exc.IllegalScoreboardSettingInput

    for problem_id in target_problem_ids:
        problem = await db.problem.read(problem_id=problem_id, include_deleted=True)
        challenge = await db.challenge.read(challenge_id=problem.challenge_id, include_scheduled=True)
        if challenge.class_id is not scoreboard_challenge.class_id:
            raise exc.IllegalScoreboardSettingInput

    return await db.scoreboard_setting_team_project.add_under_scoreboard(
        challenge_id=challenge_id, challenge_label=challenge_label, title=title, target_problem_ids=target_problem_ids,
        type=type, scoring_formula=scoring_formula, baseline_team_id=baseline_team_id,
        rank_by_total_score=rank_by_total_score, team_label_filter=team_label_filter,
    )


async def calculate_score(team_raw_score: dict[int, int], formula: str,
                          baseline_team_id: int = None) -> dict[int, int]:
    """
    Return: dict[team_id, score]
    """
    class_best = max(team_raw_score.values())
    class_worst = min(team_raw_score.values())
    if baseline_team_id is not None:
        baseline = team_raw_score[baseline_team_id]

    team_score_dict = dict()
    for team_id in team_raw_score:
        team_score = team_raw_score[team_id]
        try:
            team_score_dict[team_id] = eval(formula)
        except TypeError or NameError or ZeroDivisionError:
            raise exc.IllegalFormula

    return team_score_dict


async def view_team_scoreboard(scoreboard_id: int) -> Sequence[vo.ViewTeamProjectScoreboard]:

    scoreboard, scoreboard_setting_data = await service.scoreboard.read_with_scoreboard_setting_data(scoreboard_id=scoreboard_id)
    challenge = await service.challenge.read(challenge_id=scoreboard.challenge_id, include_scheduled=True)
    teams = await db.team.browse_with_team_label_filter(team_label_filter=scoreboard_setting_data.team_label_filter,
                                                        class_id=challenge.class_id)

    team_data = {team.id: [] for team in teams}

    for target_problem_id in scoreboard.target_problem_ids:
        team_submission, team_judgment = await service.judgment.get_class_last_team_submission_judgment(
            problem_id=target_problem_id, class_id=challenge.class_id, team_ids=[team.id for team in teams])
        testcases = await db.testcase.browse(problem_id=target_problem_id)

        team_score_problem = {team.id: 0 for team in teams}
        for testcase in testcases:
            judge_cases = await db.judge_case.batch_get_with_judgment(
                testcase_id=testcase.id, judgment_ids=[judgment.id for team_id, judgment in team_judgment.items()])

            team_raw_score = {team_id: judge_cases[judgment.id].score
                              for team_id, judgment in team_judgment.items()}

            team_score = await calculate_score(team_raw_score=team_raw_score, formula=scoreboard_setting_data.scoring_formula,
                                               baseline_team_id=scoreboard_setting_data.baseline_team_id)
            for team in teams:
                team_score_problem[team.id] += team_score[team.id]

        for team in teams:
            team_data[team.id].append(vo.ProblemScore(problem_id=target_problem_id,
                                                      score=team_score_problem[team.id],
                                                      submission_id=team_submission[team.id].id))

    return [vo.ViewTeamProjectScoreboard(team_id=team.id,
                                         team_name=team.name,
                                         total_score=sum([problem_score.score for problem_score in team_data[team.id]]),
                                         target_problem_data=[problem_score for problem_score in team_data[team.id]])
            for team in teams]



