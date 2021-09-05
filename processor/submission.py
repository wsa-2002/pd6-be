from typing import Sequence

import pydantic
from fastapi import File, UploadFile, Depends
from pydantic import BaseModel

from base import do, popo
from base.enum import RoleType, ChallengePublicizeType, FilterOperator
import const
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model, file_upload_limit

router = APIRouter(
    tags=['Submission'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/submission/language', tags=['Administrative'])
@enveloped
async def browse_all_submission_language(request: Request) -> Sequence[do.SubmissionLanguage]:
    """
    ### 權限
    - System normal
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await service.submission.browse_language()


class AddSubmissionLanguageInput(BaseModel):
    name: str
    version: str
    is_disabled: bool


@router.post('/submission/language', tags=['Administrative'])
@enveloped
async def add_submission_language(data: AddSubmissionLanguageInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - System manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    language_id = await service.submission.add_language(name=data.name, version=data.version,
                                                        is_disabled=data.is_disabled)
    return model.AddOutput(id=language_id)


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

    return await service.submission.edit_language(language_id,
                                                  name=data.name, version=data.version, is_disabled=data.is_disabled)


@router.post('/problem/{problem_id}/submission', tags=['Problem'],
             dependencies=[Depends(file_upload_limit.valid_file_length(file_length=const.CODE_UPLOAD_LIMIT))])
@enveloped
async def submit(problem_id: int, language_id: int, request: Request, content_file: UploadFile = File(...)) \
        -> model.AddOutput:
    """
    ### 權限
    - System Manager (all)
    - System normal (non scheduled)

    ### 限制
    - 上傳檔案 < 1mb
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Validate problem
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = request.time >= publicize_time

    if not (is_challenge_publicized
            or await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)):
        raise exc.NoPermission

    # Validate language
    language = await service.submission.read_language(language_id)
    if language.is_disabled:
        raise exc.IllegalInput

    submission_id = await service.submission.add(file=content_file.file, filename=content_file.filename,
                                                 account_id=request.account.id, problem_id=problem.id,
                                                 file_length=len(content_file.file.read()),
                                                 language_id=language.id, submit_time=request.time)
    await service.judgment.judge_submission(submission_id)

    return model.AddOutput(id=submission_id)


BROWSE_SUBMISSION_COLUMNS = {
    'problem_id': int,
    'language_id': int,
    'submit_time': model.ServerTZDatetime,
}


@router.get('/submission')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_COLUMNS.items()})
async def browse_submission(account_id: int, request: Request, limit: model.Limit = 50, offset: model.Offset = 0,
                            filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> model.BrowseOutputBase:
    """
    ### 權限
    - Self: see self

    ### Available columns
    """
    if account_id is not request.account.id:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_SUBMISSION_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_SUBMISSION_COLUMNS)

    # 只能看自己的
    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=request.account.id))

    submissions, total_count = await service.submission.browse(limit=limit, offset=offset,
                                                               filters=filters, sorters=sorters)

    return model.BrowseOutputBase(submissions, total_count=total_count)


@router.get('/submission/judgment/batch')
@enveloped
async def batch_get_submission_judgment(request: Request, submission_ids: pydantic.Json) -> Sequence[do.Judgment]:
    """
    ### 權限
    - System Normal

    ### Notes
    - `submission_ids`: list of int
    """
    submission_ids = pydantic.parse_obj_as(list[int], submission_ids)

    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    return await service.submission.browse_with_submission_ids(submission_ids=submission_ids)


@router.get('/submission/{submission_id}')
@enveloped
async def read_submission(submission_id: int, request: Request) -> do.Submission:
    """
    ### 權限
    - Self
    - Class manager
    """
    submission = await service.submission.read(submission_id=submission_id)

    # 可以看自己的
    if submission.account_id is request.account.id:
        return submission

    # 助教可以看他的 class 的
    problem = await service.problem.read(problem_id=submission.problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)
    if class_role >= RoleType.manager:
        return submission

    raise exc.NoPermission


@router.get('/submission/{submission_id}/judgment', tags=['Judgment'])
@enveloped
async def browse_all_submission_judgment(submission_id: int, request: Request) -> Sequence[do.Judgment]:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    submission = await service.submission.read(submission_id=submission_id)
    problem = await service.problem.read(problem_id=submission.problem_id)
    challenge = await service.challenge.read(challenge_id=problem.challenge_id, include_scheduled=True)

    if not rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission
    return await service.judgment.browse(submission_id=submission_id)


@router.get('/submission/{submission_id}/latest-judgment', tags=['Judgment'])
@enveloped
async def read_submission_latest_judgment(submission_id: int, request: Request) -> do.Judgment:
    """
    ### 權限
    - Self: see self
    - Class manager: see class
    """
    submission = await service.submission.read(submission_id=submission_id)

    # 可以看自己的
    if submission.account_id is request.account.id:
        return await service.submission.read_latest_judgment(submission_id=submission_id)

    problem = await service.problem.read(problem_id=submission.problem_id)
    challenge = await service.challenge.read(challenge_id=problem.challenge_id, include_scheduled=True)

    # 助教可以看管理的 class 的
    if rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        return await service.submission.read_latest_judgment(submission_id=submission_id)

    raise exc.NoPermission


@router.post('/submission/{submission_id}/rejudge')
@enveloped
async def rejudge_submission(submission_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    submission = await service.submission.read(submission_id=submission_id)
    problem = await service.problem.read(problem_id=submission.problem_id)
    challenge = await service.challenge.read(challenge_id=problem.challenge_id, include_scheduled=True)

    if not rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await service.judgment.judge_submission(submission.id)

