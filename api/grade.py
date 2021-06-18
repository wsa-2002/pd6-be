from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, envelope, auth
import persistence.database as db
from util import rbac


router = APIRouter(
    tags=['Grade'],
    default_response_class=envelope.JSONResponse,
)


@router.post('/class/{class_id}/grade', tags=['Class'])
async def import_class_grade(class_id: int, request: auth.Request):
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission
    """
    匯入方式未定
    """
    ...


@router.get('/class/{class_id}/grade', tags=['Class'])
async def browse_class_grade(class_id: int, request: auth.Request) -> Sequence[do.Grade]:
    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=class_id)
    if not is_class_manager:
        return await db.grade.browse(class_id=class_id, receiver_id=request.account.id)

    return await db.grade.browse(class_id=class_id)


@router.get('/account/{account_id}/grade', tags=['Account'])
async def browse_account_grade(account_id: int, request: auth.Request) -> Sequence[do.Grade]:
    if request.account.id is not account_id:  # only self
        raise exc.NoPermission
    return await db.grade.browse(receiver_id=account_id)


@router.get('/grade/{grade_id}')
async def get_grade(grade_id: int, request: auth.Request) -> do.Grade:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await db.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    is_self = request.account.id is grade.receiver_id
    if not is_class_manager and not is_self:
        raise exc.NoPermission

    return grade


class EditGradeInput(BaseModel):
    title: str = None
    score: Optional[int] = ...
    comment: Optional[str] = ...
    is_hidden: bool = None


@router.patch('/grade/{grade_id}')
async def edit_grade(grade_id: int, data: EditGradeInput, request: auth.Request) -> None:
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await db.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    if not is_class_manager:
        raise exc.NoPermission

    await db.grade.edit(grade_id=grade_id, title=data.title, score=data.score, comment=data.comment,
                        update_time=datetime.now(), is_hidden=data.is_hidden)  # TODO: request.time?


@router.delete('/grade/{grade_id}')
async def delete_grade(grade_id: int, request: auth.Request):
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await db.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    if not is_class_manager:
        raise exc.NoPermission

    await db.grade.delete(grade_id)
