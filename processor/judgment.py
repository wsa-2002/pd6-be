from typing import Sequence

from base import do, enum
from middleware import APIRouter, response, enveloped, auth
import service

router = APIRouter(
    tags=['Judgment'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/judgment/status', tags=['Administrative', 'Public'])
@enveloped
async def browse_all_judgment_status() -> Sequence[enum.JudgmentStatusType]:
    """
    ### 權限
    - Public
    """
    return list(enum.JudgmentStatusType)


@router.get('/judgment/{judgment_id}')
@enveloped
async def read_judgment(judgment_id: int) -> do.Judgment:
    """
    ### 權限
    - Self (latest)
    - Class manager (all)
    """
    return await service.judgment.read(judgment_id=judgment_id)


@router.get('/judgment/{judgment_id}/judge-case')
@enveloped
async def browse_all_judgment_judge_case(judgment_id: int) -> Sequence[do.JudgeCase]:
    """
    ### 權限
    - Self (latest)
    - Class manager (all)
    """
    return await service.judgment.browse_cases(judgment_id=judgment_id)
