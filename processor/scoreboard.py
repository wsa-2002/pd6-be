from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from fastapi import UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from base import do
from base.enum import RoleType, ChallengePublicizeType, TaskSelectionType, ScoreboardType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac, model


router = APIRouter(
    tags=['Scoreboard'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddTeamProjectScoreboardInput(BaseModel):
    label: str
    title: str
    target_problem_ids: Sequence[int]
    type: ScoreboardType

    # team_project_scoreboard
    scoring_formula: str
    baseline_team_id: Optional[int]
    rank_by_total_score: bool
    team_label_filter: Optional[str]


@router.post('/challenge/{challenge_id}/team-project-scoreboard')
@enveloped
async def add_team_project_scoreboard_under_challenge(challenge_id: int,
                                                      data: AddTeamProjectScoreboardInput,
                                                      request: Request) -> model.AddOutput:

    team_project_scoreboard_id = await service.scoreboard_setting_team_project.add(
        scoring_formula=data.scoring_formula,
        baseline_team_id=data.baseline_team_id,
        rank_by_total_score=data.rank_by_total_score,
        team_label_filter=data.team_label_filter,
    )

    scoreboard_id = await service.scoreboard.add(
        challenge_id=challenge_id,
        label=data.label,
        title=data.title,
        target_problem_ids=data.target_problem_ids,
        type=data.type,
        setting_id=team_project_scoreboard_id,
    )

    return model.AddOutput(id=scoreboard_id)
