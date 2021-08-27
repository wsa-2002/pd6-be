from uuid import UUID

from fastapi import File, UploadFile

from base.enum import RoleType, ChallengePublicizeType, FilterOperator
from base import do, popo
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model


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


BROWSE_ESSAY_SUBMISSION_COLUMNS = {
    'id': int,
    'account_id': int,
    'essay_id': int,
    'content_file_uuid': UUID,
    'filename': str,
    'submit_time': model.ServerTZDatetime,
}


@router.get('/essay/{essay_id}/essay-submission')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_ESSAY_SUBMISSION_COLUMNS.items()})
async def browse_essay_submission_by_essay_id(
        essay_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - class manager (all)
    - class normal (self)

    ### Available columns
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    essay = await service.essay.read(essay_id=essay_id)
    challenge = await service.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)

    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    if (not class_role is RoleType.manager and not class_role is RoleType.normal):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ESSAY_SUBMISSION_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ESSAY_SUBMISSION_COLUMNS)

    filters.append(popo.Filter(col_name='essay_id',
                               op=FilterOperator.eq,
                               value=essay_id))

    if class_role is RoleType.normal:
        filters.append(popo.Filter(col_name='account_id',
                                   op=FilterOperator.eq,
                                   value=request.account.id))

    essay_submissions, total_count = await service.essay_submission.browse(limit=limit, offset=offset,
                                                                           filters=filters, sorters=sorters)
    return model.BrowseOutputBase(essay_submissions, total_count=total_count)


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
