from dataclasses import dataclass
from typing import Optional, Sequence, Any
import json

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
async def add_team_project_scoreboard_under_challenge(challenge_id: int, data: AddTeamProjectScoreboardInput,
                                                      request: Request) -> model.AddOutput:

    scoreboard_id = await service.scoreboard_setting_team_project.add_under_scoreboard(
        challenge_id=challenge_id, label=data.label, title=data.title, target_problem_ids=data.target_problem_ids,
        type=data.type, scoring_formula=data.scoring_formula, baseline_team_id=data.baseline_team_id,
        rank_by_total_score=data.rank_by_total_score, team_label_filter=data.team_label_filter,
    )

    return model.AddOutput(id=scoreboard_id)


@dataclass
class ReadScoreboardOutput:
    id: int
    challenge_id: int
    label: str
    title: str
    target_problem_ids: Sequence[int]
    is_deleted: bool
    type: ScoreboardType
    data: Any


@router.get('/scoreboard/{scoreboard_id}')
@enveloped
async def read_scoreboard(scoreboard_id: int, request: Request) -> ReadScoreboardOutput:

    scoreboard, data = await service.scoreboard.read_with_scoreboard_setting_data(scoreboard_id=scoreboard_id)
    return ReadScoreboardOutput(id=scoreboard.id,
                                challenge_id=scoreboard.challenge_id,
                                label=scoreboard.label,
                                title=scoreboard.title,
                                target_problem_ids=scoreboard.target_problem_ids,
                                is_deleted=scoreboard.is_deleted,
                                type=scoreboard.type,
                                data=data)


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





