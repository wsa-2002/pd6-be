from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from pydantic import BaseModel

from base import do, popo
from base.enum import RoleType, FilterOperator
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Peer Review'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/peer-review/{peer_review_id}')
@enveloped
async def read_peer_review(peer_review_id: int) -> do.PeerReview:
    """
    ### 權限
    - Class manager (hidden)
    - Class normal (not hidden)
    """
    class_role = await service.rbac.get_class_role(context.account.id, peer_review_id=peer_review_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    peer_review = await db.peer_review.read(peer_review_id)
    challenge = await db.challenge.read(peer_review.challenge_id)
    is_scheduled = challenge.start_time > context.request_time

    if not (is_scheduled and class_role >= RoleType.manager  # hidden => need manager
            or not is_scheduled and class_role >= RoleType.normal):  # not hidden => need normal
        raise exc.NoPermission

    return peer_review


class EditPeerReviewInput(BaseModel):
    challenge_label: str = None
    title: str = None
    description: str = None
    min_score: int = None
    max_score: int = None
    max_review_count: int = None


@router.patch('/peer-review/{peer_review_id}')
@enveloped
async def edit_peer_review(peer_review_id: int, data: EditPeerReviewInput) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, peer_review_id=peer_review_id):
        raise exc.NoPermission

    return await db.peer_review.edit(peer_review_id=peer_review_id,
                                     challenge_label=data.challenge_label,
                                     title=data.title,
                                     description=data.description,
                                     min_score=data.min_score, max_score=data.max_score,
                                     max_review_count=data.max_review_count)


@router.delete('/peer-review/{peer_review_id}')
@enveloped
async def delete_peer_review(peer_review_id: int) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, peer_review_id=peer_review_id):
        raise exc.NoPermission

    return await db.peer_review.delete(peer_review_id=peer_review_id)


BROWSE_PEER_REVIEW_RECORD_COLUMNS = {
    'grader_id': int,
    'receiver_id': int,
    'score': int,
    'comment': str,
    'submit_time': model.ServerTZDatetime,
}


@dataclass
class BrowsePeerReviewRecordData:
    id: int
    peer_review_id: int
    grader_id: Optional[int]
    submission_id: int
    receiver_id: int
    score: Optional[int]
    comment: Optional[str]
    submit_time: Optional[datetime]


class BrowsePeerReviewRecordOutput(model.BrowseOutputBase):
    data: Sequence[BrowsePeerReviewRecordData]


@router.get('/peer-review/{peer_review_id}/record')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_PEER_REVIEW_RECORD_COLUMNS.items()})
async def browse_peer_review_record(peer_review_id: int,
                                    limit: model.Limit, offset: model.Offset,
                                    filter: model.FilterStr = None, sort: model.SorterStr = None, ) \
        -> BrowsePeerReviewRecordOutput:
    """
    ### 權限
    - Class manager (full)
    - Self (看不到對方)

    ### Available columns
    """
    is_manager = await service.rbac.validate_class(context.account.id, RoleType.manager, peer_review_id=peer_review_id)

    filters = model.parse_filter(filter, BROWSE_PEER_REVIEW_RECORD_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_PEER_REVIEW_RECORD_COLUMNS)

    if not is_manager:  # 不是 class manager 的話只能看自己的
        filters.append(popo.Filter(col_name='receiver_id',
                                   op=FilterOperator.eq,
                                   value=context.account.id))

    peer_review_record, total_count = await db.peer_review_record.browse(peer_review_id=peer_review_id,
                                                                         limit=limit, offset=offset,
                                                                         filters=filters, sorters=sorters)

    records = [BrowsePeerReviewRecordData(id=record.id, peer_review_id=record.peer_review_id,
                                          submission_id=record.submission_id,
                                          grader_id=record.grader_id if is_manager else None,  # self 不能看 grader_id
                                          receiver_id=record.receiver_id,
                                          score=record.score, comment=record.comment, submit_time=record.submit_time)
               for record in peer_review_record]

    return BrowsePeerReviewRecordOutput(records, total_count=total_count)


@dataclass
class AssignPeerReviewOutput:
    id: list[int]


# 改一下這些 function name
@router.post('/peer-review/{peer_review_id}/record')
@enveloped
async def assign_peer_review_record(peer_review_id: int) -> AssignPeerReviewOutput:
    """
    發互評 (決定 A 要評誰 )

    ### 權限
    - Self is class *normal ONLY*
    """
    class_role = await service.rbac.get_class_role(context.account.id, peer_review_id=peer_review_id)
    if class_role is not RoleType.normal:
        raise exc.NoPermission

    peer_review = await db.peer_review.read(peer_review_id)
    challenge = await db.challenge.read(challenge_id=peer_review.challenge_id)
    if not challenge.start_time <= context.request_time <= challenge.end_time:
        raise exc.NoPermission

    peer_review_records = await db.peer_review_record.read_by_peer_review_id(peer_review_id=peer_review.id,
                                                                             account_id=context.account.id,
                                                                             is_receiver=False)

    if len(peer_review_records) >= peer_review.max_review_count:
        raise exc.MaxPeerReviewCount

    peer_review_record_ids = [await db.peer_review_record.add_auto(peer_review_id=peer_review.id,
                                                                   grader_id=context.account.id)
                              for _ in range(peer_review.max_review_count)]

    return AssignPeerReviewOutput(peer_review_record_ids)


@dataclass
class ReadPeerReviewRecordOutput:
    id: int
    peer_review_id: int
    submission_id: int
    grader_id: Optional[int]
    receiver_id: Optional[int]
    score: Optional[int]
    comment: Optional[str]
    submit_time: Optional[datetime]
    filename: str
    file_uuid: UUID


@router.get('/peer-review-record/{peer_review_record_id}')
@enveloped
async def read_peer_review_record(peer_review_record_id: int) -> ReadPeerReviewRecordOutput:
    """
    ### 權限
    - Class manager (full)
    - Self = Class normal (看不到對方)
    """
    class_role = await service.rbac.get_class_role(context.account.id, peer_review_record_id=peer_review_record_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    is_manager = class_role >= RoleType.manager
    peer_review_record = await db.peer_review_record.read(peer_review_record_id)
    peer_review = await db.peer_review.read(peer_review_id=peer_review_record.peer_review_id)
    challenge = await db.challenge.read(challenge_id=peer_review.challenge_id)
    is_grader = context.account.id == peer_review_record.grader_id
    is_receiver = context.account.id == peer_review_record.receiver_id
    if not (is_manager
            or is_grader
            or (is_receiver and challenge.end_time <= context.request_time)):
        raise exc.NoPermission

    submission = await db.submission.read(submission_id=peer_review_record.submission_id)
    return ReadPeerReviewRecordOutput(
        id=peer_review_record.id,
        peer_review_id=peer_review_record.id,
        submission_id=submission.id,
        grader_id=peer_review_record.grader_id if not is_receiver else None,
        receiver_id=peer_review_record.receiver_id if not is_grader else None,
        score=peer_review_record.score,
        comment=peer_review_record.comment,
        submit_time=peer_review_record.submit_time,
        filename=submission.filename,
        file_uuid=submission.content_file_uuid,
    )


class SubmitPeerReviewInput(BaseModel):
    score: int
    comment: str


@router.patch('/peer-review-record/{peer_review_record_id}')
@enveloped
async def submit_peer_review_record(peer_review_record_id: int, data: SubmitPeerReviewInput) -> None:
    """
    互評完了，交互評成績評語

    ### 權限
    - Self is class *normal ONLY*
    """
    class_role = await service.rbac.get_class_role(context.account.id, peer_review_record_id=peer_review_record_id)
    if class_role is not RoleType.normal:  # only class normal
        raise exc.NoPermission

    peer_review_record = await db.peer_review_record.read(peer_review_record_id)
    peer_review = await db.peer_review.read(peer_review_id=peer_review_record.peer_review_id)
    challenge = await db.challenge.read(challenge_id=peer_review.challenge_id)
    if not challenge.start_time <= context.request_time <= challenge.end_time:
        raise exc.NoPermission
    # 檢查 score 是否在規定範圍內
    if not (peer_review.min_score <= data.score <= peer_review.max_score):
        raise exc.IllegalInput

    await db.peer_review_record.edit_score(peer_review_record.id, score=data.score,
                                           comment=data.comment, submit_time=context.request_time)


@router.get('/peer-review/{peer_review_id}/account/{account_id}/receive')
@enveloped
async def browse_account_received_peer_review_record(peer_review_id: int, account_id: int) \
        -> list[int]:
    """
    ### 權限
    - Class Manager (all)
    - Self = Class normal
    """
    class_role = await service.rbac.get_class_role(context.account.id, peer_review_id=peer_review_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    peer_review = await db.peer_review.read(peer_review_id)
    challenge = await db.challenge.read(challenge_id=peer_review.challenge_id)

    if not (class_role >= RoleType.manager
            or (context.account.id == account_id and challenge.end_time <= context.request_time)):
        raise exc.NoPermission

    peer_review_records = await db.peer_review_record.read_by_peer_review_id(peer_review_id,
                                                                             account_id=account_id,
                                                                             is_receiver=True)
    return [peer_review_record.id for peer_review_record in peer_review_records]


@router.get('/peer-review/{peer_review_id}/account/{account_id}/review')
@enveloped
async def browse_account_reviewed_peer_review_record(peer_review_id: int, account_id: int) \
        -> list[int]:
    """
    ### 權限
    - Class Manager (all)
    - Self = Class normal
    """
    class_role = await service.rbac.get_class_role(context.account.id, peer_review_id=peer_review_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    peer_review = await db.peer_review.read(peer_review_id)
    challenge = await db.challenge.read(challenge_id=peer_review.challenge_id)

    if not (class_role >= RoleType.manager
            or (context.account.id == account_id and challenge.start_time <= context.request_time)):
        raise exc.NoPermission

    peer_review_records = await db.peer_review_record.read_by_peer_review_id(peer_review_id,
                                                                             account_id=account_id,
                                                                             is_receiver=False)
    return [peer_review_record.id for peer_review_record in peer_review_records]
