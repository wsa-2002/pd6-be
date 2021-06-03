from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
from base.enum import CourseType, RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Grade'],
    default_response_class=envelope.JSONResponse,
)


@router.post('/class/{class_id}/grade', tags=['Class'])
async def import_class_grade(class_id: int):
    """
    匯入方式未定
    """
    ...


@router.get('/class/{class_id}/grade', tags=['Class'])
async def browse_class_grades(class_id: int) -> Sequence[do.Grade]:
    return await db.grade.browse(class_id=class_id)


@router.get('/account/{account_id}/grade', tags=['Account'])
async def browse_account_grades(account_id: int) -> Sequence[do.Grade]:
    return await db.grade.browse(account_id=account_id)


@router.get('/grade/{grade_id}')
async def get_grade(grade_id: int) -> do.Grade:
    return await db.grade.read(grade_id=grade_id)


class EditGradeInput(BaseModel):
    item_name: Optional[str] = None
    score: Optional[int] = None
    comment: Optional[str] = None


@router.patch('/grade/{grade_id}')
async def edit_grade(grade_id: int, data: EditGradeInput) -> None:
    await db.grade.edit(grade_id=grade_id, item_name=data.item_name, score=data.score, comment=data.comment,
                        update_time=datetime.now())  # TODO: request.time?


@router.delete('/grade/{grade_id}')
async def delete_grade(grade_id: int):
    ...  # TODO: hard delete?
