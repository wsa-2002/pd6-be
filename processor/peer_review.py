from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from base import do, popo
from base.enum import RoleType, FilterOperator
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import model, rbac


router = APIRouter(
    tags=['Peer Review'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/peer-review/{peer_review_id}')
@enveloped
async def read_peer_review(peer_review_id: int, request: Request) -> do.PeerReview:
    """
    ### 權限
    - Class manager (hidden)
    - Class normal (not hidden)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await service.peer_review.read(peer_review_id)
    challenge = await service.challenge.read(peer_review.challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    is_scheduled = challenge.start_time > request.time

    if not (is_scheduled and class_role >= RoleType.manager  # hidden => need manager
            or not is_scheduled and class_role >= RoleType.normal):  # not hidden => need normal
        raise exc.NoPermission

    return peer_review


class EditPeerReviewInput(BaseModel):
    title: str = None
    description: str = None
    min_score: int = None
    max_score: int = None
    max_review_count: int = None
    start_time: model.ServerTZDatetime = None
    end_time: model.ServerTZDatetime = None


@router.patch('/peer-review/{peer_review_id}')
@enveloped
async def edit_peer_review(peer_review_id: int, data: EditPeerReviewInput, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await service.peer_review.read(peer_review_id)
    challenge = await service.challenge.read(peer_review.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await service.peer_review.edit(peer_review_id=peer_review_id,
                                          title=data.title,
                                          description=data.description,
                                          min_score=data.min_score, max_score=data.max_score,
                                          max_review_count=data.max_review_count,
                                          start_time=data.start_time, end_time=data.end_time)


@router.delete('/peer-review/{peer_review_id}')
@enveloped
async def delete_peer_review(peer_review_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await service.peer_review.read(peer_review_id)
    challenge = await service.challenge.read(peer_review.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await service.peer_review.delete(peer_review_id=peer_review_id)


BROWSE_PEER_REVIEW_RECORD_COLUMNS = {
    'grader_id': int,
    'receiver_id': int,
    'score': int,
    'comment': str,
    'submit_time': model.ServerTZDatetime,
}


@router.get('/peer-review/{peer_review_id}/record')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_PEER_REVIEW_RECORD_COLUMNS.items()})
async def browse_peer_review_record(peer_review_id: int, request: Request,
                                    limit: model.Limit, offset: model.Offset,
                                    filter: model.FilterStr = None, sort: model.SorterStr = None,)\
        -> model.BrowseOutputBase:
    """
    ### 權限
    - Class manager (full)
    - Self (看不到對方)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await service.peer_review.read(peer_review_id=peer_review_id)
    challenge = await service.challenge.read(challenge_id=peer_review.challenge_id, include_scheduled=True)

    is_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)

    filters = model.parse_filter(filter, BROWSE_PEER_REVIEW_RECORD_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_PEER_REVIEW_RECORD_COLUMNS)

    if not is_manager:  # 不是 class manager 的話只能看自己的
        filters.append(popo.Filter(col_name='receiver_id',
                                   op=FilterOperator.eq,
                                   value=request.account.id))

    peer_review_record, total_count = await service.peer_review_record.browse(limit=limit, offset=offset,
                                                                              filters=filters, sorters=sorters)
    records = [ReadPeerReviewRecordOutput(id=record.id, peer_review_id=record.peer_review_id,
                                          grader_id=record.grader_id if is_manager else None,  # self 不能看 grader_id
                                          receiver_id=record.receiver_id,
                                          score=record.score, comment=record.comment, submit_time=record.submit_time)
               for record in peer_review_record]

    return model.BrowseOutputBase(records, total_count=total_count)


# 改一下這些 function name
@router.post('/peer-review/{peer_review_id}/record')
@enveloped
async def assign_peer_review_record(peer_review_id: int, request: Request) -> model.AddOutput:
    """
    發互評 (決定 A 要評誰 )

    ### 權限
    - Self is class *normal ONLY*
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await service.peer_review.read(peer_review_id)
    challenge = await service.challenge.read(challenge_id=peer_review.challenge_id, include_scheduled=True)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    if class_role is not RoleType.normal:
        raise exc.NoPermission

    peer_review_record_id = await service.peer_review_record.add_auto(peer_review_id=peer_review.id,
                                                                      grader_id=request.account.id)

    return model.AddOutput(id=peer_review_record_id)


@dataclass
class ReadPeerReviewRecordOutput:
    id: int
    peer_review_id: int
    grader_id: Optional[int]
    receiver_id: int
    score: int
    comment: str
    submit_time: datetime


@router.get('/peer-review-record/{peer_review_record_id}')
@enveloped
async def read_peer_review_record(peer_review_record_id: int, request: Request) -> ReadPeerReviewRecordOutput:
    """
    ### 權限
    - Class manager (full)
    - Self (看不到對方)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review_record = await service.peer_review_record.read(peer_review_record_id)
    peer_review = await service.peer_review.read(peer_review_id=peer_review_record.peer_review_id)
    challenge = await service.challenge.read(challenge_id=peer_review.challenge_id, include_scheduled=True)

    is_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)

    if not (is_manager or (request.account.id is peer_review_record.receiver_id)):
        raise exc.NoPermission

    return ReadPeerReviewRecordOutput(
        id=peer_review_record.id,
        peer_review_id=peer_review_record.id,
        grader_id=peer_review_record.grader_id if is_manager else None,
        receiver_id=peer_review_record.receiver_id,
        score=peer_review_record.score,
        comment=peer_review_record.comment,
        submit_time=peer_review_record.submit_time,
    )


class SubmitPeerReviewInput(BaseModel):
    score: int
    comment: str


@router.patch('/peer-review-record/{peer_review_record_id}')
@enveloped
async def submit_peer_review_record(peer_review_record_id: int, data: SubmitPeerReviewInput, request: Request) -> None:
    """
    互評完了，交互評成績評語

    ### 權限
    - Self is class *normal ONLY*
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review_record = await service.peer_review_record.read(peer_review_record_id)
    peer_review = await service.peer_review.read(peer_review_id=peer_review_record.peer_review_id)
    challenge = await service.challenge.read(challenge_id=peer_review.challenge_id, include_scheduled=True)

    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)
    if class_role is not RoleType.normal:  # only class normal
        raise exc.NoPermission

    await service.peer_review_record.edit(peer_review_record.id, score=data.score,
                                          comment=data.comment, submit_time=request.time)
