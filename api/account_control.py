from base.enum import Role
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db


router = APIRouter(
    tags=['Account-Control'],
    default_response_class=envelope.JSONResponse,
    route_class=auth.LoginRequiredRouter,
)


@router.get('/account/{account_id}')
def get_account(account_id: int, request: auth.AuthedRequest):
    ask_for_self = request.account.id == account_id
    if request.account.role is Role.guest and not ask_for_self:
        raise exc.rbac.NoPermission

    target_account = await db.account.get_info(account_id)
    result = {
        'id': target_account.id,
        'name': target_account.name,
        'nickname': target_account.nickname,
        'role-id': target_account.role.int,
    }

    show_personal = ask_for_self or request.account.role is Role.manager
    if show_personal:
        result.update({
            'real-name': target_account.real_name,
            'is-enabled': target_account.is_enabled,
            'alternative-email': target_account.alternative_email,
        })

    return result


@router.patch('/account/{account_id}')
def patch_account(account_id: int, request: auth.AuthedRequest):
    data = await request.json()
    if request.account.role is not Role.manager and request.account.id != account_id:
        raise exc.rbac.NoPermission

    ...  # TODO


@router.delete('/account/{account_id}')
def remove_account(account_id: int, request: auth.AuthedRequest):
    if request.account.role is not Role.manager and request.account.id != account_id:
        raise exc.rbac.NoPermission

    await db.account.set_enabled(account_id=account_id, is_enabled=False)


@router.get('/role')
@util.enveloped
def get_system_level_roles():
    return [{
        'name': 'System Manager',
        'level': 'ADMIN',
    }]


@router.post('/institute')
def add_institute(request: auth.AuthedRequest):
    if request.account.role is not Role.manager:
        raise exc.rbac.NoPermission

    data = await request.json()
    name, email_domain = data['name'], data['email-domain']
    institute_id = await db.institute.add_institute(name=name, email_domain=email_domain)
    return {'id': institute_id}


ntu = {
    'id': 1,
    'name': 'NTU',
    'email-domain': 'ntu.edu.tw',
    'is-enabled': True,
}


@router.get('/institute')
@util.enveloped
def get_institutes():
    return [ntu]


@router.get('/institute/{institute_id}')
@util.enveloped
def get_institute(institute_id: int):
    return ntu


@router.patch('/institute/{institute_id}')
@util.enveloped
def update_institute(institute_id: int):
    pass


@router.post('/account/{account_id}/student-card')
@util.enveloped
def add_student_card_to_account(account_id: int):
    return {'id': 1}


@router.get('/account/{account_id}/student-card')
@util.enveloped
def get_account_student_card(account_id: int):
    return [{
        'id': 1,
        'institute-id': 1,
        'department': 'IM',
        'student-id': 'B03705051',
        'email': 'B03705051@ntu.edu.tw',
        'is-enabled': True,
    }]


@router.get('/student-card/{student_card_id}')
@util.enveloped
def get_student_card(student_card_id: int):
    return {
        'id': 1,
        'institute-id': 1,
        'department': 'IM',
        'student-id': 'B03705051',
        'email': 'B03705051@ntu.edu.tw',
        'is-enabled': True,
    }


@router.patch('/student-card/{student_card_id}')
@util.enveloped
def update_student_card(student_card_id: int):
    pass


@router.delete('/student-card/{student_card_id}')
@util.enveloped
def remove_student_card(student_card_id: int):
    pass
