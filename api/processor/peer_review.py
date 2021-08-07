from pydantic import BaseModel

from base import do
from base.cls import NoTimezoneIsoDatetime
from base.enum import RoleType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
from .util import rbac

from .. import service

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
    description: str = None
    min_score: int = None
    max_score: int = None
    max_review_count: int = None
    start_time: NoTimezoneIsoDatetime = None
    end_time: NoTimezoneIsoDatetime = None


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


@router.get('/peer-review/{peer_review_id}/record')
@enveloped
async def browse_peer_review_record(peer_review_id: int, request: Request):
    """
    ### 權限
    - Class manager (full)
    - Self (看不到對方)
    """
    ...  # TODO


# 改一下這些 function name
@router.post('/peer-review/{peer_review_id}/record')
@enveloped
async def assign_peer_review_record(peer_review_id: int, request: Request):
    """
    發互評 (決定 A 要評誰 )

    ### 權限
    - Self is class *normal ONLY*
    """
    return {'id': 1}


@router.get('/peer-review-record/{peer_review_record_id}')
@enveloped
async def read_peer_review_record(peer_review_record_id: int, request: Request):
    """
    ### 權限
    - Class manager (full)
    - Self (看不到對方)
    """
    ...  # TODO


@router.put('/peer-review-record/{peer_review_record_id}/score')
@enveloped
async def submit_peer_review_record_score(peer_review_record_id: int, request: Request):
    """
    互評完了，交互評成績評語

    ### 權限
    - Self is class *normal ONLY*
    """
    pass
