from fastapi import APIRouter, Depends

import model
import util


router = APIRouter(tags=['Course'], dependencies=[
    Depends(util.verify_login),
])


@router.post('/course')
@util.enveloped
def create_course():
    return {'id': 1}


@router.get('/course')
@util.enveloped
def get_courses():
    return [model.pbc]


@router.get('/course/{course_id}')
@util.enveloped
def get_course(course_id: int):
    return model.pbc


@router.patch('/course/{course_id}')
@util.enveloped
def edit_course(course_id: int):
    pass


@router.delete('/course/{course_id}')
@util.enveloped
def remove_course(course_id: int):
    pass


@router.get('/course/{course_id}/member')
@util.enveloped
def get_course_members(course_id: int):
    return [{
        'account': model.account_simple,
        'role': model.ta,
    }]


@router.patch('/course/{course_id}/member')
@util.enveloped
def modify_course_member(course_id: int):
    pass


@router.delete('/course/{course_id}/member')
@util.enveloped
def remove_course_member(course_id: int):
    pass


@router.post('/course/{course_id}/class')
@util.enveloped
def create_class_under_course(course_id: int):
    return {'id': 1}


@router.get('/course/{course_id}/class')
@util.enveloped
def get_classes_under_course(course_id: int):
    return [model.pbc109]


@router.get('/class')
@util.enveloped
def get_classes():
    return [model.pbc109]


@router.get('/class/{class_id}')
@util.enveloped
def get_class(class_id: int):
    return model.pbc109


@router.patch('/class/{class_id}')
@util.enveloped
def modify_class(class_id: int):
    pass


@router.delete('/class/{class_id}')
@util.enveloped
def remove_class(class_id: int):
    pass


@router.get('/class/{class_id}/member')
@util.enveloped
def get_class_members(class_id: int):
    return [{
        'account': model.account_simple,
        'role': model.ta,
    }]


@router.patch('/class/{class_id}/member')
@util.enveloped
def modify_class_member(class_id: int):
    pass


@router.delete('/class/{class_id}/member')
@util.enveloped
def remove_class_member(class_id: int):
    pass


@router.post('/class/{class_id}/team')
@util.enveloped
def create_team_under_class(class_id: int):
    return {'id': 1}


@router.get('/class/{class_id}/team')
@util.enveloped
def get_teams_under_class(class_id: int):
    return [model.team_1]


@router.get('/team')
@util.enveloped
def get_teams():
    return [model.team_1]


@router.get('/team/{team_id}')
@util.enveloped
def get_team(team_id: int):
    return model.team_1


@router.patch('/team/{team_id}')
@util.enveloped
def modify_team(team_id: int):
    pass


@router.delete('/team/{team_id}')
@util.enveloped
def remove_team(team_id: int):
    pass


@router.get('/team/{team_id}/member')
@util.enveloped
def get_team_members(team_id: int):
    return [{
        'account': model.account_simple,
        'role': {
            'name': 'Leader',
            'level': 'ADMIN',
        },
    }]


@router.patch('/team/{team_id}/member')
@util.enveloped
def modify_team_member(team_id: int):
    pass


@router.delete('/team/{team_id}/member')
@util.enveloped
def remove_team_member(team_id: int):
    pass
