from dataclasses import dataclass
from typing import Sequence, Any

from base.enum import RoleType, ScoreboardType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import service

from .util import rbac

router = APIRouter(
    tags=['Scoreboard'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class ReadScoreboardOutput:
    id: int
    challenge_id: int
    challenge_label: str
    title: str
    target_problem_ids: Sequence[int]
    is_deleted: bool
    type: ScoreboardType
    data: Any


@router.get('/scoreboard/{scoreboard_id}')
@enveloped
async def read_scoreboard(scoreboard_id: int, request: Request) -> ReadScoreboardOutput:
    """
    ### 權限
    - Class normal
    """
    scoreboard = await db.scoreboard.read(scoreboard_id=scoreboard_id)
    challenge = await db.challenge.read(challenge_id=scoreboard.challenge_id, include_scheduled=True)
    if not await rbac.validate(request.account.id, RoleType.normal, class_id=challenge.class_id):
        raise exc.NoPermission

    scoreboard, data = await service.scoreboard.read_with_scoreboard_setting_data(scoreboard_id=scoreboard_id)
    return ReadScoreboardOutput(id=scoreboard.id,
                                challenge_id=scoreboard.challenge_id,
                                challenge_label=scoreboard.challenge_label,
                                title=scoreboard.title,
                                target_problem_ids=scoreboard.target_problem_ids,
                                is_deleted=scoreboard.is_deleted,
                                type=scoreboard.type,
                                data=data)


@router.delete('/scoreboard/{scoreboard_id}')
@enveloped
async def delete_scoreboard(scoreboard_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    scoreboard = await db.scoreboard.read(scoreboard_id=scoreboard_id)
    challenge = await db.challenge.read(challenge_id=scoreboard.challenge_id, include_scheduled=True)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.scoreboard.delete(scoreboard_id=scoreboard_id)
