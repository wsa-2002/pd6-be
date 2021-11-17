from typing import Optional, Sequence

from pydantic import BaseModel

from base import vo
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import service
from util import model

router = APIRouter(
    tags=['Team Project Scoreboard'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/team-project-scoreboard/view/{scoreboard_id}')
@enveloped
async def view_team_project_scoreboard(scoreboard_id: int, request: Request) -> Sequence[vo.ViewTeamProjectScoreboard]:
    """
    ### 權限
    - Class normal
    """
    if not await service.rbac.validate_class(request.account.id, RoleType.normal, scoreboard_id=scoreboard_id):
        raise exc.NoPermission

    scoreboard, scoreboard_setting_data = await service.scoreboard.read_with_scoreboard_setting_data(
        scoreboard_id=scoreboard_id)

    result = await service.scoreboard.view_team_project_scoreboard(scoreboard_id=scoreboard_id)
    return [vo.ViewTeamProjectScoreboard(
        team_id=team_project_scoreboard.team_id,
        team_name=team_project_scoreboard.team_name,
        total_score=team_project_scoreboard.total_score if scoreboard_setting_data.rank_by_total_score else None,
        target_problem_data=team_project_scoreboard.target_problem_data,
    ) for team_project_scoreboard in result]


class EditScoreboardInput(BaseModel):
    challenge_label: str = None
    title: str = None
    target_problem_ids: Sequence[int] = None
    scoring_formula: str = None
    baseline_team_id: Optional[int] = model.can_omit
    rank_by_total_score: bool = None
    team_label_filter: Optional[str] = model.can_omit


@router.patch('/team-project-scoreboard/{scoreboard_id}')
@enveloped
async def edit_team_project_scoreboard(scoreboard_id: int, data: EditScoreboardInput, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(request.account.id, RoleType.manager, scoreboard_id=scoreboard_id):
        raise exc.NoPermission

    if not await service.scoreboard.validate_formula(formula=data.scoring_formula):
        raise exc.InvalidFormula

    await db.scoreboard_setting_team_project.edit_with_scoreboard(
        scoreboard_id=scoreboard_id, challenge_label=data.challenge_label, title=data.title,
        target_problem_ids=data.target_problem_ids, scoring_formula=data.scoring_formula,
        baseline_team_id=data.baseline_team_id, rank_by_total_score=data.rank_by_total_score,
        team_label_filter=data.team_label_filter
    )
