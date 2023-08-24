from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from fastapi import UploadFile, File
from pydantic import BaseModel

from base import do, popo
import exceptions as exc
from base.enum import RoleType, FilterOperator
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Grade'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.post('/class/{class_id}/grade-import', tags=['Class'])
@enveloped
async def import_class_grade(class_id: int, title: str, grade_file: UploadFile = File(...)) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    await service.csv.import_class_grade(grade_file=grade_file.file, class_id=class_id,
                                         title=title, update_time=context.request_time)


class AddGradeInput(BaseModel):
    receiver_referral: str
    grader_referral: str
    title: str
    score: str
    comment: str


@router.post('/class/{class_id}/grade')
@enveloped
async def add_grade(class_id: int, data: AddGradeInput) -> model.AddOutput:
    """
    ### 權限
    - Class Manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    grade_id = await db.grade.add(receiver=data.receiver_referral, grader=data.grader_referral, class_id=class_id,
                                  title=data.title, score=data.score, comment=data.comment,
                                  update_time=context.request_time)

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


class BrowseClassGradeOutput(model.BrowseOutputBase):
    data: Sequence[do.Grade]


@router.get('/class/{class_id}/grade', tags=['Class'])
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_GRADE_COLUMNS.items()})
async def browse_class_grade(class_id: int,
                             limit: int = 50, offset: int = 0,
                             filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> BrowseClassGradeOutput:
    """
    ### 權限
    - Class manager (all)
    - Class normal (self)

    ### Available columns
    """
    class_role = await service.rbac.get_class_role(context.account.id, class_id=class_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CLASS_GRADE_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_GRADE_COLUMNS)
    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    if class_role >= RoleType.manager:
        grades, total_count = await db.grade.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)
        return BrowseClassGradeOutput(grades, total_count=total_count)
    else:  # Self
        filters.append(popo.Filter(col_name='receiver_id',
                                   op=FilterOperator.eq,
                                   value=context.account.id))
        grades, total_count = await db.grade.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)
        return BrowseClassGradeOutput(grades, total_count=total_count)


BROWSE_ACCOUNT_GRADE_COLUMNS = {
    'class_id': int,
    'title': str,
    'score': str,
    'comment': str,
    'update_time': str,
}


class BrowseAccountGradeOutput(model.BrowseOutputBase):
    data: Sequence[do.Grade]


@router.get('/account/{account_id}/grade', tags=['Account'])
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCOUNT_GRADE_COLUMNS.items()})
async def browse_account_grade(account_id: int,
                               limit: model.Limit = 50, offset: model.Offset = 0,
                               filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> BrowseAccountGradeOutput:
    """
    ### 權限
    - Self

    ### Available columns
    """
    if context.account.id != account_id:  # only self
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ACCOUNT_GRADE_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ACCOUNT_GRADE_COLUMNS)
    filters.append(popo.Filter(col_name='receiver_id',
                               op=FilterOperator.eq,
                               value=context.account.id))
    grades, total_count = await db.grade.browse(limit=limit, offset=offset, filters=filters, sorters=sorters)

    return BrowseAccountGradeOutput(grades, total_count=total_count)


@dataclass
class GetGradeTemplateOutput:
    s3_file_uuid: UUID
    filename: str


@router.get('/grade/template')
@enveloped
async def get_grade_template_file() -> GetGradeTemplateOutput:
    """
    ### 權限
    - system normal
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    s3_file, filename = await service.csv.get_grade_template()
    return GetGradeTemplateOutput(s3_file_uuid=s3_file.uuid, filename=filename)


@router.get('/grade/{grade_id}')
@enveloped
async def get_grade(grade_id: int) -> do.Grade:
    """
    ### 權限
    - Class manager (all)
    - Class normal (self)
    """
    class_role = await service.rbac.get_class_role(context.account.id, grade_id=grade_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    is_class_manager = class_role >= RoleType.manager

    grade = await db.grade.read(grade_id=grade_id)
    is_self = context.account.id == grade.receiver_id

    if not (is_class_manager or is_self):
        raise exc.NoPermission

    return grade


class EditGradeInput(BaseModel):
    title: str = None
    score: Optional[str] = model.can_omit
    comment: Optional[str] = model.can_omit


@router.patch('/grade/{grade_id}')
@enveloped
async def edit_grade(grade_id: int, data: EditGradeInput) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, grade_id=grade_id):
        raise exc.NoPermission

    await db.grade.edit(grade_id=grade_id, grader_id=context.account.id, title=data.title, score=data.score,
                        comment=data.comment, update_time=context.request_time)


@router.delete('/grade/{grade_id}')
@enveloped
async def delete_grade(grade_id: int):
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, grade_id=grade_id):
        raise exc.NoPermission

    await db.grade.delete(grade_id)
