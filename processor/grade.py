import csv
import codecs
from typing import Optional, Sequence

from fastapi import UploadFile, File
from pydantic import BaseModel

from base import do
import exceptions as exc
from base.enum import RoleType
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac


router = APIRouter(
    tags=['Grade'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


GRADE_TEMPLATE_UUID = 'c36fba7c-6516-4b5c-bc87-f31323ba3aec'
GRADE_TEMPLATE = ['Receiver', 'Title', 'Score', 'Comment', 'Grader']


@router.post('/class/{class_id}/grade', tags=['Class'])
@enveloped
async def import_class_grade(class_id: int, request: Request, grade_file: UploadFile = File(...)):
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    rows = csv.DictReader(codecs.iterdecode(grade_file.file, 'utf_8_sig'))
    for row in rows:
        await service.grade.add(receiver=row['Receiver'], grader=row['Grader'], class_id=class_id,
                                comment=row['Comment'], score=row['Score'], title=row['Title'],
                                update_time=request.time)


@router.get('/class/{class_id}/grade', tags=['Class'])
@enveloped
async def browse_class_grade(class_id: int, request: Request) -> Sequence[do.Grade]:
    """
    ### 權限
    - Class manager (all)
    - Class normal (self)
    """
    if await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):  # Class manager
        return await service.grade.browse(class_id=class_id)
    else:  # Self
        return await service.grade.browse(class_id=class_id, receiver_id=request.account.id)


@router.get('/account/{account_id}/grade', tags=['Account'])
@enveloped
async def browse_account_grade(account_id: int, request: Request) -> Sequence[do.Grade]:
    """
    ### 權限
    - Self
    """
    if request.account.id is not account_id:  # only self
        raise exc.NoPermission

    return await service.grade.browse(receiver_id=account_id)


@router.get('/grade/{grade_id}')
@enveloped
async def get_grade(grade_id: int, request: Request) -> do.Grade:
    """
    ### 權限
    - Class manager (all)
    - Class normal (self)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await service.grade.read(grade_id=grade_id)

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
async def edit_grade(grade_id: int, data: EditGradeInput, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await service.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    if not is_class_manager:
        raise exc.NoPermission

    await service.grade.edit(grade_id=grade_id, title=data.title, score=data.score, comment=data.comment,
                             update_time=request.time)


@router.delete('/grade/{grade_id}')
@enveloped
async def delete_grade(grade_id: int, request: Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    grade = await service.grade.read(grade_id=grade_id)

    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=grade.class_id)
    if not is_class_manager:
        raise exc.NoPermission

    await service.grade.delete(grade_id)
