from fastapi import APIRouter, Depends

import model
import util


router = APIRouter(tags=['Challenge-Problem'], dependencies=[
    Depends(util.verify_login),
])


@router.post('/class/{class_id}/challenge', tags=['Course'])
@util.enveloped
def create_challenge_under_class(class_id: int):
    return {'id': 1}


@router.get('/class/{class_id}/challenge', tags=['Course'])
@util.enveloped
def get_challenges_under_class(class_id: int):
    return [model.challenge]


@router.get('/challenge')
@util.enveloped
def get_challenges():
    return [model.challenge]


@router.get('/challenge/{challenge_id}')
@util.enveloped
def get_challenge(challenge_id: int):
    return model.challenge


@router.patch('/challenge/{challenge_id}')
@util.enveloped
def modify_challenge(challenge_id: int):
    pass


@router.delete('/challenge/{challenge_id}')
@util.enveloped
def remove_challenge(challenge_id: int):
    pass


@router.post('/challenge/{challenge_id}/problem')
@util.enveloped
def create_problem_under_challenge(challenge_id: int):
    return {'id': 1}


@router.get('/challenge/{challenge_id}/problem')
@util.enveloped
def get_problems_under_challenge(challenge_id: int):
    return [model.problem]


@router.get('/problem')
@util.enveloped
def get_problems():
    return [model.problem]


@router.get('/problem/{problem_id}')
@util.enveloped
def get_problem(problem_id: int):
    return model.problem


@router.patch('/problem/{problem_id}')
@util.enveloped
def modify_problem(problem_id: int):
    pass


@router.delete('/problem/{problem_id}')
@util.enveloped
def remove_problem(problem_id: int):
    pass


@router.post('/problem/{problem_id}/testdata')
@util.enveloped
def create_testdata_under_problem(problem_id: int):
    return {'id': 1}


@router.get('/problem/{problem_id}/testdata')
@util.enveloped
def get_testdata_under_problem(problem_id: int):
    return [model.testdata_1, model.testdata_2]


@router.get('/testdata/{testdata_id}')
@util.enveloped
def get_testdata(testdata_id: int):
    if testdata_id is 1:
        return model.testdata_1
    elif testdata_id is 2:
        return model.testdata_2
    else:
        raise Exception


@router.patch('/testdata/{testdata_id}')
@util.enveloped
def modify_testdata(testdata_id: int):
    pass


@router.delete('/testdata/{testdata_id}')
@util.enveloped
def remove_testdata(testdata_id: int):
    pass
