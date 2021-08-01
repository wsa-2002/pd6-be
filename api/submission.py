from typing import Sequence

from pydantic import BaseModel

from base import do
from base.enum import RoleType, ChallengePublicizeType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import util
from util import rbac


router = APIRouter(
    tags=['Submission'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/submission/language', tags=['Administrative'])
@enveloped
async def browse_submission_language(request: Request) -> Sequence[do.SubmissionLanguage]:
    """
    ### 權限
    - System normal
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.submission.browse_language()


class AddSubmissionLanguageInput(BaseModel):
    name: str
    version: str
    is_disabled: bool


@router.post('/submission/language', tags=['Administrative'])
@enveloped
async def add_submission_language(data: AddSubmissionLanguageInput, request: Request) -> int:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.submission.add_language(name=data.name, version=data.version, is_disabled=data.is_disabled)


class EditSubmissionLanguageInput(BaseModel):
    name: str = None
    version: str = None
    is_disabled: bool = None


@router.patch('/submission/language/{language_id}', tags=['Administrative'])
@enveloped
async def edit_submission_language(language_id: int, data: EditSubmissionLanguageInput, request: Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.submission.edit_language(language_id,
                                             name=data.name, version=data.version, is_disabled=data.is_disabled)


class AddSubmissionInput(BaseModel):
    language_id: int
    content_file: str  # TODO


@router.post('/problem/{problem_id}/submission', tags=['Problem'])
@enveloped
async def submit(problem_id: int, data: AddSubmissionInput, request: Request):
    """
    ### 權限
    - System Manager (all)
    - System normal (non scheduled)
    """
    submit_time = request.time

    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Validate problem
    problem = await db.problem.read(problem_id)
    challenge = await db.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = submit_time >= publicize_time

    if not (is_challenge_publicized
            or await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)):
        raise exc.NoPermission

    # Validate language
    language = await db.submission.read_language(data.language_id)
    if language.is_disabled:
        raise exc.IllegalInput

    return await db.submission.add(account_id=request.account.id, problem_id=problem.id,
                                   language_id=data.language_id,
                                   content_file=data.content_file, content_length=len(data.content_file),
                                   submit_time=submit_time)


class BrowseSubmissionInput(BaseModel):
    # TODO: add more
    account_id: int = None
    problem_id: int = None
    language_id: int = None


@router.get('/submission')
@enveloped
async def browse_submission(data: BrowseSubmissionInput, request: Request) -> Sequence[do.Submission]:
    """
    ### 權限
    - Self
    - Class manager
    """
    return await db.submission.browse(
        account_id=request.account.id,  # TODO: 現在只有開放看自己的
        problem_id=data.problem_id,
        language_id=data.language_id,
    )


@router.get('/submission/{submission_id}')
@enveloped
async def read_submission(submission_id: int, request: Request) -> do.Submission:
    """
    ### 權限
    - Self
    - Class manager
    """
    submission = await db.submission.read(submission_id=submission_id)

    # 可以看自己的
    if submission.account_id is request.account.id:
        return submission

    # 可以看自己管理的 class 的
    problem = await db.problem.read(problem_id=submission.problem_id)
    challenge = await db.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)
    if class_role >= RoleType.manager:
        return submission

    raise exc.NoPermission


@router.get('/submission/{submission_id}/judgment', tags=['Judgment'])
@enveloped
async def browse_submission_judgment(submission_id: int, request: Request) -> Sequence[do.Judgment]:
    """
    ### 權限
    - Self (latest)
    - Class manager (all)
    """
    # TODO: 權限控制
    return await db.judgment.browse(submission_id=submission_id)
