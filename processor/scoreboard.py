from dataclasses import dataclass
from typing import Optional, Sequence, Any

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


@router.delete('/scoreboard/{scoreboard_id}')
@enveloped
async def delete_scoreboard(scoreboard_id: int, request: Request) -> None:

    await service.scoreboard.delete(scoreboard_id=scoreboard_id)


