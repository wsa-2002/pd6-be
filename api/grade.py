from datetime import datetime
from typing import Optional, Sequence

from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import util
from util import rbac


router = APIRouter(
    tags=['Grade'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


@router.post('/class/{class_id}/grade', tags=['Class'])
@enveloped
async def import_class_grade(class_id: int, request: auth.Request):
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission
    """
    匯入方式未定
    """
    ...


@router.get('/class/{class_id}/grade', tags=['Class'])
@enveloped
async def browse_class_grade(class_id: int, request: auth.Request) -> Sequence[do.Grade]:
    """
    ### 權限
    - Class manager (hidden)
    - Self (not hidden)
    """
    if await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):  # Class manager
        return await db.grade.browse(class_id=class_id)
    else:  # Self
        return await db.grade.browse(class_id=class_id, receiver_id=request.account.id)


@router.get('/account/{account_id}/grade', tags=['Account'])
@enveloped
async def browse_account_grade(account_id: int, request: auth.Request) -> Sequence[do.Grade]:
    """
    ### 權限
    - Self
    """
    if request.account.id is not account_id:  # only self
        raise exc.NoPermission

    return await db.grade.browse(receiver_id=account_id)


@router.get('/grade/{grade_id}')
@enveloped
async def get_grade(grade_id: int, request: auth.Request) -> do.Grade:
    """
    ### 權限
    - Class manager (hidden)
    - Self (not hidden)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await db.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    is_self = request.account.id is grade.receiver_id

    if not (is_class_manager or is_self):
        raise exc.NoPermission

    return grade


class EditGradeInput(BaseModel):
    title: str = None
    score: Optional[int] = ...
    comment: Optional[str] = ...


@router.patch('/grade/{grade_id}')
@enveloped
async def edit_grade(grade_id: int, data: EditGradeInput, request: auth.Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await db.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    if not is_class_manager:
        raise exc.NoPermission

    await db.grade.edit(grade_id=grade_id, title=data.title, score=data.score, comment=data.comment,
                        update_time=util.get_request_time())  # TODO: request.time?


@router.delete('/grade/{grade_id}')
@enveloped
async def delete_grade(grade_id: int, request: auth.Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await db.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    if not is_class_manager:
        raise exc.NoPermission

    await db.grade.delete(grade_id)
