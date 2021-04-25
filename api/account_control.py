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
    if request.account.role.is_guest and not ask_for_self:
        raise exc.NoPermission

    target_account = await db.account.get_by_id(account_id)
    result = {
        'id': target_account.id,
        'name': target_account.name,
        'nickname': target_account.nickname,
        'role': target_account.role,
    }

    show_personal = ask_for_self or request.account.role.is_manager
    if show_personal:
        result.update({
            'real-name': target_account.real_name,
            'is-enabled': target_account.is_enabled,
            'alternative-email': target_account.alternative_email,
        })

    return result


@router.patch('/account/{account_id}')
def patch_account(account_id: int, request: auth.AuthedRequest):
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    data = await request.json()
    if nickname := data.get('nickname', ''):
        await db.account.set_by_id(account_id=account_id, nickname=nickname)


@router.delete('/account/{account_id}')
def remove_account(account_id: int, request: auth.AuthedRequest):
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    await db.account.set_enabled(account_id=account_id, is_enabled=False)


@router.post('/institute')
def add_institute(request: auth.AuthedRequest):
    if not request.account.role.is_manager:
        raise exc.NoPermission

    data = await request.json()
    name, email_domain = data['name'], data['email-domain']
    institute_id = await db.institute.add(name=name, email_domain=email_domain)
    return {'id': institute_id}


@router.get('/institute')
def get_institutes(request: auth.AuthedRequest):
    return [inst.as_resp_dict()
            for inst in await db.institute.get_all(only_enabled=request.account.role.not_manager)]


@router.get('/institute/{institute_id}')
def get_institute(institute_id: int, request: auth.AuthedRequest):
    inst = await db.institute.get_by_id(institute_id, only_enabled=request.account.role.not_manager)
    return inst.as_resp_dict()


@router.patch('/institute/{institute_id}')
def update_institute(institute_id: int, request: auth.AuthedRequest):
    if not request.account.role.is_manager:
        raise exc.NoPermission

    data = await request.json()
    await db.institute.set_by_id(institute_id=institute_id,
                                 name=data.get('name', None),
                                 email_domain=data.get('email-domain', None),
                                 is_enabled=data.get('is-enabled', None))


@router.post('/account/{account_id}/student-card')
def add_student_card_to_account(account_id: int, request: auth.AuthedRequest):
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    data = await request.json()
    student_card_id = await db.student_card.add(
        institute_id=data['institute-id'],
        department=data['department'],
        student_id=data['student-id'],
        email=data['email'],
        is_enabled=data['is-enabled'],
    )
    return {'id': student_card_id}


@router.get('/account/{account_id}/student-card')
def get_account_student_card(account_id: int, request: auth.AuthedRequest):
    if request.account.role.not_manager and request.account.id != account_id:
        raise exc.NoPermission

    student_cards = await db.student_card.get_by_account_id(account_id)
    return [card.as_resp_dict() for card in student_cards]


@router.get('/student-card/{student_card_id}')
def get_student_card(student_card_id: int, request: auth.AuthedRequest):
    owner_id = await db.student_card.get_owner_id(student_card_id=student_card_id)
    if request.account.role.not_manager and request.account.id != owner_id:
        raise exc.NoPermission

    return (await db.student_card.get_by_id(student_card_id=student_card_id)).as_resp_dict()


@router.patch('/student-card/{student_card_id}')
def update_student_card(student_card_id: int, request: auth.AuthedRequest):
    # 暫時只開給 manager
    if not request.account.role.is_manager:
        raise exc.NoPermission

    data = await request.json()
    await db.student_card.set_by_id(
        student_card_id=student_card_id,
        institute_id=data.get('institute-id', None),
        department=data.get('department-id', None),
        student_id=data.get('student-id', None),
        email=data.get('email', None),
        is_enabled=data.get('is-enabled', None),
    )


@router.delete('/student-card/{student_card_id}')
def remove_student_card(student_card_id: int, request: auth.AuthedRequest):
    owner_id = await db.student_card.get_owner_id(student_card_id=student_card_id)
    if request.account.role.not_manager and request.account.id != owner_id:
        raise exc.NoPermission

    await db.student_card.set_by_id(student_card_id, is_enabled=False)
