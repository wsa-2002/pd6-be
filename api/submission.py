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


@router.post('/problem/{problem_id}/submission', tags=['Problem'])
async def submit(problem_id: int):
    return {'id': 1}


@router.get('/submission/language', tags=['Administrative'])
async def browse_submission_language() -> Sequence[do.SubmissionLanguage]:
    return await db.submission.browse_language()


class AddSubmissionLanguageInput(BaseModel):
    name: str
    version: str


@router.post('/submission/language', tags=['Administrative'])
async def add_submission_language(data: AddSubmissionLanguageInput) -> int:
    return await db.submission.add_language(name=data.name, version=data.version)


@router.delete('/submission/language/{language_id}', tags=['Administrative'])
async def delete_submission_language(language_id: int) -> None:
    return await db.submission.delete_language(language_id=language_id)


class BrowseSubmissionInput(BaseModel):
    # TODO: add more
    account_id: int = None
    problem_id: int = None
    task_id: int = None
    language_id: int = None


@router.get('/submission')
async def browse_submission(data: BrowseSubmissionInput) -> Sequence[do.Submission]:
    return await db.submission.browse(
        account_id=data.account_id,
        problem_id=data.problem_id,
        task_id=data.task_id,
        language_id=data.language_id,
    )


@router.get('/submission/{submission_id}')
async def read_submission(submission_id: int) -> do.Submission:
    return await db.submission.read(submission_id=submission_id)


@router.get('/submission/{submission_id}/judgment', tags=['Judgment'])
async def browse_submission_judgment(submission_id: int) -> Sequence[do.Judgment]:
    return await db.judgment.browse(submission_id=submission_id)
