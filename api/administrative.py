from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

import model
import util


router = APIRouter(tags=['Administrative'], dependencies=[
    Depends(util.verify_login),
])



ann_1 = {
    'id': 1,
    'title': '公告1',
    'content': '內容1',
    'author': model.account_simple,
    'post-time': model.time.past_long,
    'expire-time': model.time.past,
}
ann_2 = {
    'id': 2,
    'title': '公告2',
    'content': '內容2',
    'author': model.account_simple,
    'post-time': model.time.past,
    'expire-time': model.time.future,
}


@router.post('/announcement')
@util.enveloped
def add_announcement():
    return {'id': 1}


@router.get('/announcement')
@util.enveloped
def browse_announcements():
    return [ann_1, ann_2]


@router.get('/announcement/{announcement_id}')
@util.enveloped
def read_announcement(announcement_id: int):
    if announcement_id is 1:
        return ann_1
    elif announcement_id is 2:
        return ann_2
    else:
        raise Exception


@router.patch('/announcement/{announcement_id}')
@util.enveloped
def edit_announcement(announcement_id: int):
    pass


@router.delete('/announcement/{announcement_id}')
@util.enveloped
def delete_announcement(announcement_id: int):
    pass


@router.get('/peer-review')
@util.enveloped
def browse_peer_reviews():
    return [model.peer_review]


@router.post('/peer-review')
@util.enveloped
def add_peer_review():
    return {'id': 1}


@router.post('/peer-review/{peer_review_id}')
@util.enveloped
def read_peer_review(peer_review_id: int):
    return model.peer_review


@router.patch('/peer-review/{peer_review_id}')
@util.enveloped
def edit_peer_review(peer_review_id: int):
    pass


@router.delete('/peer-review/{peer_review_id}')
@util.enveloped
def delete_peer_review(peer_review_id: int):
    pass


@router.get('/peer-review/{peer_review_id}/record')
@util.enveloped
def browse_peer_review_records(peer_review_id: int):
    return [model.peer_review_record]


@router.post('/peer-review/{peer_review_id}/record')
@util.enveloped
def add_peer_review_record(peer_review_id: int):
    return {'id': 1}


@router.get('/peer-review-record/{peer_review_record_id}/record')
@util.enveloped
def read_peer_review_record(peer_review_record_id: int):
    return model.peer_review_record


@router.patch('/peer-review-record/{peer_review_record_id}/record')
@util.enveloped
def edit_peer_review_record(peer_review_record_id: int):
    pass
