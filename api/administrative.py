from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

import model
import util


router = APIRouter(tags=['Administrative'], dependencies=[
    Depends(util.verify_login),
])


score_1 = {
    'id': 1,
    'receiver-id': 1,
    'grader': model.account_simple,
    'class-id': 1,
    'item-name': '測試成績',
    'score': 'A',
    'comment': '測試評語',
    'update-time': model.time.past,
}
score_2 = {
    'id': 2,
    'receiver-id': 1,
    'grader': model.account_simple,
    'class-id': 1,
    'item-name': '測試成績2',
    'score': 10,
    'comment': '測試評語2',
    'update-time': model.time.now,
}


@router.post('/class/{class_id}/score')
@util.enveloped
def import_class_score(class_id: int):
    """
    匯入方式未定
    """
    pass


@router.get('/class/{class_id}/score')
@util.enveloped
def get_class_scores(class_id: int):
    return [score_1, score_2]


@router.get('/account/{account_id}/score')
@util.enveloped
def get_account_scores(account_id: int):
    return [score_1, score_2]


@router.get('/score/{score_id}')
@util.enveloped
def get_score(score_id: int):
    if score_id is 1:
        return score_1
    elif score_id is 2:
        return score_2
    else:
        raise Exception


@router.patch('/score/{score_id}')
@util.enveloped
def modify_score(score_id: int):
    pass


@router.delete('/score/{score_id}')
@util.enveloped
def remove_score(score_id: int):
    pass


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
def create_announcement():
    return {'id': 1}


@router.get('/announcement')
@util.enveloped
def get_announcements():
    return [ann_1, ann_2]


@router.get('/announcement/{announcement_id}')
@util.enveloped
def get_announcement(announcement_id: int):
    if announcement_id is 1:
        return ann_1
    elif announcement_id is 2:
        return ann_2
    else:
        raise Exception


@router.patch('/announcement/{announcement_id}')
@util.enveloped
def update_announcement(announcement_id: int):
    pass


@router.delete('/announcement/{announcement_id}')
@util.enveloped
def remove_announcement(announcement_id: int):
    pass


@router.get('/peer-review')
@util.enveloped
def get_peer_reviews():
    return [model.peer_review]


@router.post('/peer-review')
@util.enveloped
def create_peer_review():
    return {'id': 1}


@router.post('/peer-review/{peer_review_id}')
@util.enveloped
def get_peer_review(peer_review_id: int):
    return model.peer_review


@router.patch('/peer-review/{peer_review_id}')
@util.enveloped
def modify_peer_review(peer_review_id: int):
    pass


@router.delete('/peer-review/{peer_review_id}')
@util.enveloped
def remove_peer_review(peer_review_id: int):
    pass


@router.get('/peer-review/{peer_review_id}/record')
@util.enveloped
def get_peer_review_records(peer_review_id: int):
    return [model.peer_review_record]


@router.post('/peer-review/{peer_review_id}/record')
@util.enveloped
def submit_peer_review_records(peer_review_id: int):
    return {'id': 1}


@router.get('/peer-review-record/{peer_review_record_id}/record')
@util.enveloped
def get_peer_review_record(peer_review_record_id: int):
    return model.peer_review_record


@router.patch('/peer-review-record/{peer_review_record_id}/record')
@util.enveloped
def modify_peer_review_record(peer_review_record_id: int):
    pass
