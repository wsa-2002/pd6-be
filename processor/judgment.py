from typing import Sequence

from base import do, enum
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac

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
async def read_judgment(judgment_id: int, request: Request) -> do.Judgment:
    """
    ### 權限
    - Self
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    judgment = await service.judgment.read(judgment_id=judgment_id)
    submission = await service.submission.read(submission_id=judgment.submission_id)

    # 可以看自己的
    if request.account.id == submission.account_id:
        return judgment

    problem = await service.problem.read(problem_id=submission.problem_id)
    challenge = await service.challenge.read(challenge_id=problem.challenge_id, include_scheduled=True)

    # 助教可以看他的 class 的
    if await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        return judgment

    raise exc.NoPermission


@router.get('/judgment/{judgment_id}/judge-case')
@enveloped
async def browse_all_judgment_judge_case(judgment_id: int, request: Request) -> Sequence[do.JudgeCase]:
    """
    ### 權限
    - Self
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    judgment = await service.judgment.read(judgment_id=judgment_id)
    submission = await service.submission.read(submission_id=judgment.submission_id)
    problem = await service.problem.read(problem_id=submission.problem_id)
    challenge = await service.challenge.read(challenge_id=problem.challenge_id, include_scheduled=True)

    if not (await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)
            or request.account.id == submission.account_id):
        raise exc.NoPermission

    return await service.judgment.browse_cases(judgment_id=judgment_id)
