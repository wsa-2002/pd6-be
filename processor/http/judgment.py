from typing import Sequence

from base import do, enum
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from util.context import context

router = APIRouter(
    tags=['Judgment'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/judgment/verdict', tags=['Administrative', 'Public'])
@enveloped
async def browse_all_judgment_verdict() -> Sequence[enum.VerdictType]:
    """
    ### 權限
    - Public
    """
    return list(enum.VerdictType)


@router.get('/judgment/{judgment_id}')
@enveloped
async def read_judgment(judgment_id: int) -> do.Judgment:
    """
    ### 權限
    - Self
    - Class manager
    """
    judgment = await db.judgment.read(judgment_id=judgment_id)
    submission = await db.submission.read(submission_id=judgment.submission_id)

    # 可以看自己的
    if context.account.id == submission.account_id:
        return judgment

    # 助教可以看他的 class 的
    if await service.rbac.validate_class(context.account.id, RoleType.manager, submission_id=submission.id):
        return judgment

    raise exc.NoPermission


@router.get('/judgment/{judgment_id}/judge-case')
@enveloped
async def browse_all_judgment_judge_case(judgment_id: int) -> Sequence[do.JudgeCase]:
    """
    ### 權限
    - Self
    - Class manager
    """
    judgment = await db.judgment.read(judgment_id=judgment_id)
    submission = await db.submission.read(submission_id=judgment.submission_id)

    # 可以看自己的
    if context.account.id == submission.account_id:
        return await db.judgment.browse_cases(judgment_id=judgment_id)

    # 助教可以看他的 class 的
    if await service.rbac.validate_class(context.account.id, RoleType.manager, submission_id=submission.id):
        return await db.judgment.browse_cases(judgment_id=judgment_id)

    raise exc.NoPermission
