from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from fastapi import UploadFile, File
from pydantic import BaseModel

from base import do, popo
import exceptions as exc
from base.enum import RoleType, FilterOperator
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model

router = APIRouter(
    tags=['Grade'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.post('/class/{class_id}/grade-import', tags=['Class'])
@enveloped
async def import_class_grade(class_id: int, title: str, request: Request, grade_file: UploadFile = File(...)):
    """
    ### 權限
    - Class manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await service.grade.import_class_grade(grade_file=grade_file.file, class_id=class_id,
                                           title=title, update_time=request.time)


class AddGradeInput(BaseModel):
    receiver_referral: str
    grader_referral: str
    title: str
    score: str
    comment: str


@router.post('/class/{class_id}/grade')
@enveloped
async def add_grade(class_id: int, data: AddGradeInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class Manager
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    grade_id = await service.grade.add(receiver=data.receiver_referral, grader=data.grader_referral, class_id=class_id,
                                       title=data.title, score=data.score, comment=data.comment,
                                       update_time=request.time)

    return model.AddOutput(id=grade_id)


BROWSE_CLASS_GRADE_COLUMNS = {
    'receiver_id': int,
    'grader_id': int,
    'class_id': int,
    'title': str,
    'score': str,
    'comment': str,
    'update_time': str,
}


@router.get('/class/{class_id}/grade', tags=['Class'])
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_GRADE_COLUMNS.items()})
async def browse_class_grade(class_id: int, request: Request,
                             limit: int = 50, offset: int = 0,
                             filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> model.BrowseOutputBase:
    """
    ### 權限
    - Class manager (all)
    - Class normal (self)

    ### Available columns
    """

    filters = model.parse_filter(filter, BROWSE_CLASS_GRADE_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_GRADE_COLUMNS)
    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    if await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):  # Class manager
        grades, total_count = await service.grade.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)
        return model.BrowseOutputBase(grades, total_count=total_count)
    else:  # Self
        filters.append(popo.Filter(col_name='receiver_id',
                                   op=FilterOperator.eq,
                                   value=request.account.id))
        grades, total_count = await service.grade.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)
        return model.BrowseOutputBase(grades, total_count=total_count)


BROWSE_ACCOUNT_GRADE_COLUMNS = {
    'class_id': int,
    'title': str,
    'score': str,
    'comment': str,
    'update_time': str,
}


@router.get('/account/{account_id}/grade', tags=['Account'])
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCOUNT_GRADE_COLUMNS.items()})
async def browse_account_grade(account_id: int, request: Request,
                               limit: model.Limit = 50, offset: model.Offset = 0,
                               filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> model.BrowseOutputBase:
    """
    ### 權限
    - Self

    ### Available columns
    """
    if request.account.id != account_id:  # only self
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ACCOUNT_GRADE_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ACCOUNT_GRADE_COLUMNS)
    filters.append(popo.Filter(col_name='receiver_id',
                               op=FilterOperator.eq,
                               value=request.account.id))
    grades, total_count = await service.grade.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)

    return model.BrowseOutputBase(grades, total_count=total_count)


@dataclass
class GetGradeTemplateOutput:
    s3_file_uuid: UUID
    filename: str


@router.get('/grade/template')
@enveloped
async def get_grade_template_file(request: Request) -> GetGradeTemplateOutput:
    """
    ### 權限
    - system normal
    """
    if not rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    s3_file, filename = await service.grade.get_template_file()
    return GetGradeTemplateOutput(s3_file_uuid=s3_file.uuid, filename=filename)


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
    is_self = request.account.id == grade.receiver_id

    if not (is_class_manager or is_self):
        raise exc.NoPermission

    return grade


class EditGradeInput(BaseModel):
    title: str = None
    score: Optional[str] = model.can_omit
    comment: Optional[str] = model.can_omit


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

    await service.grade.edit(grade_id=grade_id, grader_id=request.account.id, title=data.title, score=data.score,
                             comment=data.comment, update_time=request.time)


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
