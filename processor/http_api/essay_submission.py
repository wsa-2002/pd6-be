from typing import Sequence
from uuid import UUID

from fastapi import File, UploadFile, Depends

from base.enum import RoleType, FilterOperator
from base import do, popo
import const
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Essay Submission'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.post('/essay/{essay_id}/essay-submission',
             dependencies=[Depends(util.file.valid_file_length(file_length=const.ESSAY_UPLOAD_LIMIT))])
@enveloped
async def upload_essay(essay_id: int, essay_file: UploadFile = File(...)) -> int:
    """
    ### 權限
    - class normal

    ### 限制
    - 上傳檔案 < 10mb
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.normal, essay_id=essay_id):
        raise exc.NoPermission

    essay = await db.essay.read(essay_id=essay_id)
    challenge = await db.challenge.read(essay.challenge_id, ref_time=context.request_time)
    if context.request_time >= challenge.end_time:
        raise exc.NoPermission

    return await service.submission.submit_essay(file=essay_file.file, filename=essay_file.filename,
                                                 account_id=context.account.id, essay_id=essay_id,
                                                 submit_time=context.request_time)


BROWSE_ESSAY_SUBMISSION_COLUMNS = {
    'id': int,
    'account_id': int,
    'essay_id': int,
    'content_file_uuid': UUID,
    'filename': str,
    'submit_time': model.ServerTZDatetime,
}


class BrowseEssaySubmissionByEssayId(model.BrowseOutputBase):
    data: Sequence[do.EssaySubmission]


@router.get('/essay/{essay_id}/essay-submission')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_ESSAY_SUBMISSION_COLUMNS.items()})
async def browse_essay_submission_by_essay_id(
        essay_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseEssaySubmissionByEssayId:
    """
    ### 權限
    - Self

    ### Available columns
    """
    class_role = await service.rbac.get_class_role(context.account.id, essay_id=essay_id)
    if not (class_role >= RoleType.normal):
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_ESSAY_SUBMISSION_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_ESSAY_SUBMISSION_COLUMNS)

    filters.append(popo.Filter(col_name='essay_id',
                               op=FilterOperator.eq,
                               value=essay_id))

    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=context.account.id))

    essay_submissions, total_count = await db.essay_submission.browse(limit=limit, offset=offset,
                                                                      filters=filters, sorters=sorters)
    return BrowseEssaySubmissionByEssayId(essay_submissions, total_count=total_count)


@router.get('/essay-submission/{essay_submission_id}')
@enveloped
async def read_essay_submission(essay_submission_id: int) -> do.EssaySubmission:
    """
    ### 權限
    - class manager (always)
    - class normal (self)
    """
    class_role = await service.rbac.get_class_role(context.account.id, essay_submission_id=essay_submission_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    essay_submission = await db.essay_submission.read(essay_submission_id=essay_submission_id)

    # Hardcode for PBC 110-1: Only allow specific managers to download final project data
    if essay_submission.essay_id in (2, 3, 4) \
            and (await db.essay.read(essay_submission.essay_id)).challenge_id == 367 \
            and context.account.id not in (14, 1760, 2646, 2648):
        class_role = min(class_role, RoleType.normal)

    if (class_role >= RoleType.manager
            or context.account.id == essay_submission.account_id):
        return essay_submission

    raise exc.NoPermission


@router.put('/essay-submission/{essay_submission_id}',
            dependencies=[Depends(util.file.valid_file_length(file_length=const.ESSAY_UPLOAD_LIMIT))])
@enveloped
async def reupload_essay(essay_submission_id: int, essay_file: UploadFile = File(...)):
    """
    ### 權限
    - Class normal = self

    ### 限制
    - 上傳檔案 < 10mb
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.normal,
                                             essay_submission_id=essay_submission_id):
        raise exc.NoPermission

    essay_submission = await db.essay_submission.read(essay_submission_id=essay_submission_id)
    essay = await db.essay.read(essay_id=essay_submission.essay_id)
    challenge = await db.challenge.read(challenge_id=essay.challenge_id)

    if not (context.account.id == essay_submission.account_id and context.request_time <= challenge.end_time):
        raise exc.NoPermission

    return await service.submission.resubmit_essay(file=essay_file.file, filename=essay_file.filename,
                                                   essay_submission_id=essay_submission_id,
                                                   submit_time=context.request_time)
