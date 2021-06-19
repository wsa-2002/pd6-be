from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do, enum
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Submission'],
    default_response_class=envelope.JSONResponse,
)


@router.get('/submission/language', tags=['Administrative'])
async def browse_submission_language(request: auth.Request) -> Sequence[do.SubmissionLanguage]:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.submission.browse_language()


class AddSubmissionLanguageInput(BaseModel):
    name: str
    version: str
    is_disabled: bool


@router.post('/submission/language', tags=['Administrative'])
async def add_submission_language(data: AddSubmissionLanguageInput, request: auth.Request) -> int:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.submission.add_language(name=data.name, version=data.version, is_disabled=data.is_disabled)


class EditSubmissionLanguageInput(BaseModel):
    name: str = None
    version: str = None
    is_disabled: bool = None


@router.patch('/submission/language/{language_id}', tags=['Administrative'])
async def edit_submission_language(language_id: int, data: EditSubmissionLanguageInput, request: auth.Request) -> None:
    if not await rbac.validate(request.account.id, RoleType.manager):
        raise exc.NoPermission

    return await db.submission.edit_language(language_id,
                                             name=data.name, version=data.version, is_disabled=data.is_disabled)


class AddSubmissionInput(BaseModel):
    task_id: int
    language_id: int
    content_file: str  # TODO


@router.post('/problem/{problem_id}/submission', tags=['Problem'])
async def submit(problem_id: int, data: AddSubmissionInput, request: auth.Request):
    submit_time = datetime.now()  # TODO: request time?

    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # Validate problem
    problem = await db.problem.read(problem_id, include_hidden=True)
    if problem.is_hidden:  # 只要 account 在任何一個 class 是 manager 就 ok
        if not any(await rbac.validate(request.account.id, RoleType.manager, class_id=related_class.id)
                   for related_class in await db.class_.browse_from_problem(problem.id)):
            raise exc.NoPermission

    # Validate language
    language = await db.submission.read_language(data.language_id)
    if language.is_disabled:
        raise exc.IllegalInput

    # Validate task
    if data.task_id is not None:
        task = await db.task.read(data.task_id, include_hidden=True)
        challenge = await db.challenge.read(task.challenge_id, include_hidden=True)
        class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)
        if (class_role < RoleType.manager and (task.is_hidden or challenge.is_hidden)   # hidden 只有 manager 可以
                or not challenge.start_time <= submit_time < challenge.end_time):  # 超出時間
            raise exc.NoPermission

    return await db.submission.add(account_id=request.account.id, problem_id=problem.id,
                                   task_id=data.task_id, language_id=data.language_id,
                                   content_file=data.content_file, content_length=len(data.content_file),
                                   submit_time=submit_time)


class BrowseSubmissionInput(BaseModel):
    # TODO: add more
    account_id: int = None
    problem_id: int = None
    task_id: int = None
    language_id: int = None


@router.get('/submission')
async def browse_submission(data: BrowseSubmissionInput, request: auth.Request) -> Sequence[do.Submission]:
    return await db.submission.browse(
        account_id=request.account.id,  # TODO: 現在只有開放看自己的
        problem_id=data.problem_id,
        task_id=data.task_id,
        language_id=data.language_id,
    )


@router.get('/submission/{submission_id}')
async def read_submission(submission_id: int, request: auth.Request) -> do.Submission:
    submission = await db.submission.read(submission_id=submission_id)

    # 可以看自己的
    if submission.account_id is request.account.id:
        return submission

    # 可以看自己管理的 class 的
    if submission.task_id is not None:
        task = await db.task.read(submission.task_id, include_hidden=True)
        challenge = await db.challenge.read(task.challenge_id, include_hidden=True)
        class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)
        if class_role >= RoleType.manager:
            return submission

    raise exc.NoPermission


@router.get('/submission/{submission_id}/judgment', tags=['Judgment'])
async def browse_submission_judgment(submission_id: int, request: auth.Request) -> Sequence[do.Judgment]:
    # TODO: 權限控制
    return await db.judgment.browse(submission_id=submission_id)
