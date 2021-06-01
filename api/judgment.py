from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do, enum
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Judgment'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/judgment/status', tags=['Administrative'])
def browse_judgment_statuses() -> Sequence[enum.JudgmentStatusType]:
    return list(enum.JudgmentStatusType)


@router.get('/judgment/{judgment_id}')
def read_judgment(judgment_id: int) -> do.Judgment:
    return await db.judgment.read(judgment_id=judgment_id)


@router.get('/judgment/{judgment_id}/judge-case')
def browse_judgment_judge_case(judgment_id: int) -> Sequence[do.JudgeCase]:
    return await db.judgment.browse_cases(judgment_id=judgment_id)
