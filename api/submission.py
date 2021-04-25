from fastapi import APIRouter, Depends

import model
import util


router = APIRouter(tags=['Submission'], dependencies=[
    Depends(util.verify_login),
])


@router.post('/problem/{problem_id}/submission', tags=['Challenge-Problem'])
@util.enveloped
def submit(problem_id: int):
    return {'id': 1}


@router.get('/submission/language', tags=['Administrative'])
@util.enveloped
def get_submission_languages():
    return [model.submission_lang]


@router.get('/submission')
@util.enveloped
def get_submissions():
    return [model.submission]


@router.get('/submission/{submission_id}')
@util.enveloped
def get_submission(submission_id: int):
    return model.submission


@router.get('/submission/{submission_id}/judgment')
@util.enveloped
def get_submission_judgments(submission_id: int):
    return [model.judgment_1]


@router.get('/judgment/result', tags=['Administrative'])
@util.enveloped
def get_judgment_results():
    return [model.judgment_result]


@router.get('/judgment/{judgment_id}')
@util.enveloped
def get_judgment(judgment_id: int):
    return model.judgment_result


@router.get('/judgment/{judgment_id}/testdata-result')
@util.enveloped
def get_judgment_testdata_result(judgment_id: int):
    return [model.judgment_testdata_result_1, model.judgment_testdata_result_2]
