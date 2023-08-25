from typing import Sequence

import pydantic
from fastapi import BackgroundTasks, File, UploadFile, Depends
from pydantic import BaseModel

from base import do, popo
from base.enum import RoleType, ChallengePublicizeType, FilterOperator
import const
import exceptions as exc
import log
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Submission'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/submission/language', tags=['Administrative'])
@enveloped
async def browse_all_submission_language() -> Sequence[do.SubmissionLanguage]:
    """
    ### 權限
    - System normal
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.submission.browse_language()


class AddSubmissionLanguageInput(BaseModel):
    name: str
    version: str
    queue_name: str
    is_disabled: bool


@router.post('/submission/language', tags=['Administrative'])
@enveloped
async def add_submission_language(data: AddSubmissionLanguageInput) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    language_id = await db.submission.add_language(name=data.name, version=data.version, queue_name=data.queue_name,
                                                   is_disabled=data.is_disabled)
    return model.AddOutput(id=language_id)


class EditSubmissionLanguageInput(BaseModel):
    name: str = None
    version: str = None
    is_disabled: bool = None


@router.patch('/submission/language/{language_id}', tags=['Administrative'])
@enveloped
async def edit_submission_language(language_id: int, data: EditSubmissionLanguageInput) -> None:
    """
    ### 權限
    - System manager
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.submission.edit_language(language_id,
                                             name=data.name, version=data.version, is_disabled=data.is_disabled)


@router.post('/problem/{problem_id}/submission', tags=['Problem'],
             dependencies=[Depends(util.file.valid_file_length(file_length=const.CODE_UPLOAD_LIMIT))])
@enveloped
async def submit(problem_id: int, language_id: int, background_tasks: BackgroundTasks,
                 content_file: UploadFile = File(...)) -> model.AddOutput:
    """
    ### 權限
    - System Manager (all)
    - System normal (non scheduled)

    ### 限制
    - 上傳檔案 < 1mb
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    # Validate problem
    problem = await db.problem.read(problem_id)
    challenge = await db.challenge.read(problem.challenge_id)
    class_role = await service.rbac.get_class_role(context.account.id, class_id=challenge.class_id)
    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = context.request_time >= publicize_time

    if not (is_challenge_publicized
            or (class_role and context.request_time >= challenge.start_time)
            or class_role == RoleType.manager):
        raise exc.NoPermission

    # Validate language
    language = await db.submission.read_language(language_id)
    if language.is_disabled:
        raise exc.IllegalInput

    file_length = len(await content_file.read())
    await content_file.seek(0)
    submission_id = await service.submission.submit(file=content_file.file, filename=content_file.filename,
                                                    account_id=context.account.id, problem_id=problem.id,
                                                    file_length=file_length,
                                                    language_id=language.id, submit_time=context.request_time)

    async def _task() -> None:
        log.info("Start judge submission")
        await service.judge.judge_submission(submission_id)
        log.info("Finish judge submission")

    util.background_task.launch(background_tasks, _task)

    return model.AddOutput(id=submission_id)


BROWSE_SUBMISSION_COLUMNS = {
    'problem_id': int,
    'language_id': int,
    'submit_time': model.ServerTZDatetime,
}


class BrowseSubmissionOutput(model.BrowseOutputBase):
    data: Sequence[do.Submission]


@router.get('/submission')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_COLUMNS.items()})
async def browse_submission(account_id: int, limit: model.Limit = 50, offset: model.Offset = 0,
                            filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> BrowseSubmissionOutput:
    """
    ### 權限
    - Self: see self

    ### Available columns
    """
    if account_id != context.account.id:
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_SUBMISSION_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_SUBMISSION_COLUMNS)

    # 只能看自己的
    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=context.account.id))

    submissions, total_count = await db.submission.browse(limit=limit, offset=offset,
                                                          filters=filters, sorters=sorters)

    return BrowseSubmissionOutput(submissions, total_count=total_count)


@router.get('/submission/judgment/batch')
@enveloped
async def batch_get_submission_judgment(submission_ids: pydantic.Json) -> Sequence[do.Judgment]:
    """
    ### 權限
    - System Normal

    ### Notes
    - `submission_ids`: list of int
    """
    submission_ids = pydantic.parse_obj_as(list[int], submission_ids)
    if not submission_ids:
        return []

    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.judgment.browse_latest_with_submission_ids(submission_ids=submission_ids)


@router.get('/submission/{submission_id}')
@enveloped
async def read_submission(submission_id: int) -> do.Submission:
    """
    ### 權限
    - Self
    - Class manager
    """
    submission = await db.submission.read(submission_id=submission_id)

    # 可以看自己的
    if submission.account_id == context.account.id:
        return submission

    # 助教可以看他的 class 的
    if await service.rbac.validate_class(context.account.id, RoleType.manager, submission_id=submission_id):
        return submission

    raise exc.NoPermission


@router.get('/submission/{submission_id}/judgment', tags=['Judgment'])
@enveloped
async def browse_all_submission_judgment(submission_id: int) -> Sequence[do.Judgment]:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, submission_id=submission_id):
        raise exc.NoPermission

    return await db.judgment.browse(submission_id=submission_id)


@router.get('/submission/{submission_id}/latest-judgment', tags=['Judgment'])
@enveloped
async def read_submission_latest_judgment(submission_id: int) -> do.Judgment:
    """
    ### 權限
    - Self: see self
    - Class manager: see class
    """
    submission = await db.submission.read(submission_id=submission_id)

    # 可以看自己的
    if submission.account_id == context.account.id:
        return await db.submission.read_latest_judgment(submission_id=submission_id)

    # 助教可以看管理的 class 的
    if await service.rbac.validate_class(context.account.id, RoleType.manager, submission_id=submission_id):
        return await db.submission.read_latest_judgment(submission_id=submission_id)

    raise exc.NoPermission


@router.post('/submission/{submission_id}/rejudge')
@enveloped
async def rejudge_submission(submission_id: int) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, submission_id=submission_id):
        raise exc.NoPermission

    await service.judge.judge_submission(submission_id)
