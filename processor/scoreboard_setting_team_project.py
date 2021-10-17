from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType, ChallengePublicizeType, TaskSelectionType, ScoreboardType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac, model


router = APIRouter(
    tags=['Team Project Scoreboard'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class EditScoreboardInput(BaseModel):
    label: str = None
    title: str = None
    target_problem_ids: Sequence[int] = None
    scoring_formula: str = None
    baseline_team_id: Optional[int] = model.can_omit
    rank_by_total_score: bool = None
    team_label_filter: Optional[str] = model.can_omit


@router.patch('/team-project-scoreboard/{scoreboard_id}')
@enveloped
async def edit_scoreboard(scoreboard_id: int, data: EditScoreboardInput, request: Request) -> None:

    await service.scoreboard_setting_team_project.edit_with_scoreboard(
        scoreboard_id=scoreboard_id, label=data.label, title=data.title, target_problem_ids=data.target_problem_ids,
        scoring_formula=data.scoring_formula, baseline_team_id=data.baseline_team_id,
        rank_by_total_score=data.rank_by_total_score, team_label_filter=data.team_label_filter
    )

