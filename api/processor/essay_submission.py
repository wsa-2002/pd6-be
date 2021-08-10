from typing import Sequence

from fastapi import File, UploadFile

from base.enum import RoleType, ChallengePublicizeType
from base import do
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
from .util import rbac

from .. import service

router = APIRouter(
    tags=['Essay Submission'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.post('/essay/{essay_id}/essay-submission')
@enveloped
async def upload_essay(essay_id: int, request: Request, essay_file: UploadFile = File(...)) -> int:
    """
    ### 權限
    - class normal
    """
    # TODO: limit file size

    essay = await service.essay.read(essay_id=essay_id)
    challenge = await service.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = request.time >= publicize_time

    if not (is_challenge_publicized
            and await rbac.validate(request.account.id, RoleType.normal, class_id=challenge.class_id)):
        raise exc.NoPermission

    return await service.essay_submission.add(file=essay_file.file, filename=essay_file.filename,
                                              account_id=request.account.id, essay_id=essay_id,
                                              submit_time=request.time)


@router.get('/essay/{essay_id}/essay-submission')
@enveloped
async def browse_essay_submission_by_essay_id(essay_id: int, request: Request) -> Sequence[do.EssaySubmission]:
    """
    ### 權限
    - class manager (all)
    - class normal (self)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    essay = await service.essay.read(essay_id=essay_id)
    challenge = await service.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)

    if await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        return await service.essay_submission.browse(essay_id=essay_id)

    if await rbac.validate(request.account.id, RoleType.normal, class_id=challenge.class_id):
        return await service.essay_submission.browse(account_id=request.account.id, essay_id=essay_id)

    raise exc.NoPermission


@router.get('/essay-submission/{essay_submission_id}')
@enveloped
async def read_essay_submission(essay_submission_id: int, request: Request) -> do.EssaySubmission:
    """
    ### 權限
    - class manager (always)
    - class normal (self)
    """
    essay_submission = await service.essay_submission.read(essay_submission_id=essay_submission_id)

    if request.account.id is essay_submission.account_id:
        return essay_submission

    essay = await service.essay.read(essay_id=essay_submission.essay_id)
    challenge = await service.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)

    if await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        return essay_submission

    raise exc.NoPermission


@router.put('/essay-submission/{essay_submission_id}')
@enveloped
async def reupload_essay(essay_submission_id: int, request: Request, essay_file: UploadFile = File(...)):
    """
    ### 權限
    - self
    """
    essay_submission = await service.essay_submission.read(essay_submission_id=essay_submission_id)

    if request.account.id is not essay_submission.account_id:
        raise exc.NoPermission

    return await service.essay_submission.edit(file=essay_file.file, filename=essay_file.filename,
                                               essay_submission_id=essay_submission_id,
                                               submit_time=request.time)
