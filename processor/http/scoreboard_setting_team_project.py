from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel, constr

from base.enum import RoleType, ScoreboardType, VerdictType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from util import model
from util.context import context

router = APIRouter(
    tags=['Team Project Scoreboard'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class ViewTeamProjectScoreboardProblemScoreOutput:
    problem_id: int
    score: float
    submission_id: int


@dataclass
class ViewTeamProjectScoreboardOutput:
    team_id: int
    team_name: str
    total_score: Optional[float]
    target_problem_data: Sequence[ViewTeamProjectScoreboardProblemScoreOutput]


@router.get('/team-project-scoreboard/view/{scoreboard_id}')
@enveloped
async def view_team_project_scoreboard(scoreboard_id: int) \
        -> Sequence[ViewTeamProjectScoreboardOutput]:
    """
    ### 權限
    - Class normal
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.normal, scoreboard_id=scoreboard_id):
        raise exc.NoPermission

    scoreboard = await db.scoreboard.read(scoreboard_id)
    if scoreboard.type != ScoreboardType.team_project:
        raise exc.IllegalInput

    setting_data = await db.scoreboard_setting_team_project.read(scoreboard.setting_id)

    class_id = (await db.challenge.read(challenge_id=scoreboard.challenge_id)).class_id
    teams = await db.team.browse_with_team_label_filter(class_id=class_id,
                                                        team_label_filter=setting_data.team_label_filter)

    team_problem_scores: dict[int, list[ViewTeamProjectScoreboardProblemScoreOutput]] = {team.id: [] for team in teams}

    for problem_id in scoreboard.target_problem_ids:

        team_submissions, team_judgments = await db.judgment.get_class_last_team_submission_judgment(
            problem_id=problem_id, class_id=class_id, team_ids=[team.id for team in teams])

        baseline_judgment_id = team_judgments.get(setting_data.baseline_team_id)

        testcases = await db.testcase.browse(problem_id=problem_id)
        teams_score = {team.id: 0 for team in teams}
        for testcase in testcases:
            if testcase.is_sample:
                continue

            judgment_id_judge_case = await db.judge_case.batch_get_with_judgment(
                testcase_id=testcase.id, judgment_ids=team_judgments.values(), verdict=VerdictType.accepted)

            calculator = service.scoreboard.get_team_project_calculator(
                formula=setting_data.scoring_formula,
                class_max=max((judge_case.score for judge_case in judgment_id_judge_case.values()), default=0),
                class_min=min((judge_case.score for judge_case in judgment_id_judge_case.values()), default=0),
                baseline=judgment_id_judge_case[baseline_judgment_id].score if baseline_judgment_id else 0,
            )

            for team_id, judgment_id in team_judgments.items():
                if judge_case := judgment_id_judge_case.get(judgment_id):
                    teams_score[team_id] += calculator(judge_case.score)

        for team_id in team_submissions:
            team_problem_scores[team_id].append(ViewTeamProjectScoreboardProblemScoreOutput(
                problem_id=problem_id,
                score=teams_score[team_id],
                submission_id=team_submissions[team_id],
            ))

    return [ViewTeamProjectScoreboardOutput(
        team_id=team.id,
        team_name=team.name,
        target_problem_data=team_problem_scores[team.id],
        total_score=sum(problem_score.score for problem_score in team_problem_scores[team.id])
        if setting_data.rank_by_total_score else None,
    ) for team in teams]


class EditScoreboardInput(BaseModel):
    challenge_label: str = None
    title: str = None
    target_problem_ids: Sequence[int] = None
    scoring_formula: constr(strip_whitespace=True, to_lower=True, strict=True) = None
    baseline_team_id: Optional[int] = model.can_omit
    rank_by_total_score: bool = None
    team_label_filter: Optional[str] = model.can_omit


@router.patch('/team-project-scoreboard/{scoreboard_id}')
@enveloped
async def edit_team_project_scoreboard(scoreboard_id: int, data: EditScoreboardInput) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, scoreboard_id=scoreboard_id):
        raise exc.NoPermission

    if data.scoring_formula and not await service.scoreboard.validate_formula(formula=data.scoring_formula):
        raise exc.InvalidFormula

    await db.scoreboard_setting_team_project.edit_with_scoreboard(
        scoreboard_id=scoreboard_id, challenge_label=data.challenge_label, title=data.title,
        target_problem_ids=data.target_problem_ids, scoring_formula=data.scoring_formula,
        baseline_team_id=data.baseline_team_id, rank_by_total_score=data.rank_by_total_score,
        team_label_filter=data.team_label_filter
    )
