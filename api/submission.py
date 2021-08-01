from typing import Sequence

from fastapi import File, UploadFile
from pydantic import BaseModel

from base import do
from base.enum import RoleType, ChallengePublicizeType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import persistence.s3 as s3
import util
from util import rbac

router = APIRouter(
    tags=['Submission'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


@router.get('/submission/language', tags=['Administrative'])
@enveloped
async def browse_submission_language(request: auth.Request) -> Sequence[do.SubmissionLanguage]:
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
async def add_submission_language(data: AddSubmissionLanguageInput, request: auth.Request) -> int:
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
async def edit_submission_language(language_id: int, data: EditSubmissionLanguageInput, request: auth.Request) -> None:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.submission.edit_language(language_id,
                                             name=data.name, version=data.version, is_disabled=data.is_disabled)


@router.post('/problem/{problem_id}/submission', tags=['Problem'])
@enveloped
async def submit(problem_id: int, language_id: int, request: auth.Request, content_file: UploadFile = File(...)):
    """
    ### 權限
    - System Manager (all)
    - System normal (non scheduled)
    """
    submit_time = util.get_request_time()

    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Validate problem
    problem = await db.problem.read(problem_id)
    challenge = await db.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=util.get_request_time())

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = submit_time >= publicize_time

    if not (is_challenge_publicized
            or await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)):
        raise exc.NoPermission

    # Validate language
    language = await db.submission.read_language(language_id)
    if language.is_disabled:
        raise exc.IllegalInput

    submission_id = await db.submission.add(account_id=request.account.id, problem_id=problem.id,
                                            language_id=language_id,
                                            content_file_id=None, content_length=None,
                                            submit_time=submit_time)

    bucket, key = await s3.submission.upload(file=content_file.file,
                                             filename=content_file.filename,
                                             submission_id=submission_id)

    content_file_id = await db.s3_file.add(bucket=bucket, key=key)

    await db.submission.edit(submission_id=submission_id,
                             content_file_id=content_file_id,
                             content_file_length=len(content_file.file.read()))


class BrowseSubmissionInput(BaseModel):
    # TODO: add more
    account_id: int = None
    problem_id: int = None
    language_id: int = None


@router.get('/submission')
@enveloped
async def browse_submission(data: BrowseSubmissionInput, request: auth.Request) -> Sequence[do.Submission]:
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
async def read_submission(submission_id: int, request: auth.Request) -> do.Submission:
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
    challenge = await db.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=util.get_request_time())
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)
    if class_role >= RoleType.manager:
        return submission

    raise exc.NoPermission


@router.get('/submission/{submission_id}/judgment', tags=['Judgment'])
@enveloped
async def browse_submission_judgment(submission_id: int, request: auth.Request) -> Sequence[do.Judgment]:
    """
    ### 權限
    - Self (latest)
    - Class manager (all)
    """
    # TODO: 權限控制
    return await db.judgment.browse(submission_id=submission_id)
