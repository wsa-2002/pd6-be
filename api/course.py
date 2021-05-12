from base.enum import CourseType, RoleType
import exceptions as exc
from middleware import APIRouter, envelope, auth
import persistence.database as db


router = APIRouter(
    tags=['Course'],
    default_response_class=envelope.JSONResponse,
    route_class=auth.LoginRequiredRouter,
)


@router.post('/course')
@auth.require_manager
async def create_course(request: auth.AuthedRequest):
    data = await request.json()
    course_id = await db.course.create(
        name=data['name'],
        course_type=data['type'],
        is_enabled=data['is-enabled'],
        is_hidden=data['is-hidden'],
    )
    return {'id': course_id}


@router.get('/course')
@auth.require_normal
async def get_courses(request: auth.AuthedRequest):
    show_limited = request.account.role.not_manager
    courses = await db.course.get_all(only_enabled=show_limited, exclude_hidden=show_limited)
    return [course.as_resp_dict() for course in courses]


@router.get('/course/{course_id}')
@auth.require_normal
async def get_course(course_id: int, request: auth.AuthedRequest):
    show_limited = request.account.role.not_manager
    course = await db.course.get_by_id(course_id, only_enabled=show_limited, exclude_hidden=show_limited)
    return course.as_resp_dict()


async def is_course_manager(course_id, account_id):
    # Check with course role
    try:
        req_account_role = await db.course.get_member_role(course_id=course_id, member_id=account_id)
    except exc.NotFound:  # Not even in course
        return False
    else:
        return req_account_role.is_manager


@router.patch('/course/{course_id}')
@auth.require_normal
async def edit_course(course_id: int, request: auth.AuthedRequest):
    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with course role
    if not await is_course_manager(course_id, request.account.id):
        raise exc.NoPermission

    data = await request.json()

    course_type = data.get('type', None)
    if course_type is not None:
        course_type = CourseType(course_type)

    await db.course.set_by_id(
        course_id=course_id,
        name=data.get('name', None),
        course_type=course_type,
        is_enabled=data.get('is-enabled', None),
        is_hidden=data.get('is-hidden', None),
    )


@router.delete('/course/{course_id}')
async def remove_course(course_id: int, request: auth.AuthedRequest):
    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with course role
    if not await is_course_manager(course_id, request.account.id):
        raise exc.NoPermission

    await db.course.set_by_id(
        course_id=course_id,
        is_enabled=False,
    )


@router.post('/course/{course_id}/member')
async def add_course_members(course_id: int, request: auth.AuthedRequest):
    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with course role
    if not await is_course_manager(course_id, request.account.id):
        raise exc.NoPermission

    data = await request.json()
    member_roles = [(record['account-id'], RoleType(record['role']))
                    for record in data]

    await db.course.add_members(course_id=course_id, member_roles=member_roles)


@router.get('/course/{course_id}/member')
async def get_course_members(course_id: int, request: auth.AuthedRequest):
    try:
        await db.course.get_member_role(course_id=course_id, member_id=request.account.id)
    except exc.NotFound:  # Not even in course
        if not request.account.role.is_manager:  # and is not manager
            raise exc.NoPermission

    member_roles = await db.course.get_member_ids(course_id=course_id)

    return [{
        'account-id': acc_id,
        'role': role,
    } for acc_id, role in member_roles]


@router.patch('/course/{course_id}/member/{member_id}')
async def modify_course_member(course_id: int, member_id: int, request: auth.AuthedRequest):
    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with course role
    if not await is_course_manager(course_id, request.account.id):
        raise exc.NoPermission

    data = await request.json()
    await db.course.set_member(course_id=course_id, member_id=member_id,
                               role=RoleType(data['role']))


@router.delete('/course/{course_id}/member/{member_id}')
@util.enveloped
async def remove_course_member(course_id: int, member_id: int, request: auth.AuthedRequest):
    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with course role
    if not await is_course_manager(course_id, request.account.id):
        raise exc.NoPermission

    await db.course.delete_member(course_id=course_id, member_id=member_id)


@router.post('/course/{course_id}/class')
@util.enveloped
async def create_class_under_course(course_id: int, request: auth.AuthedRequest):
    # Check with system role
    if not request.account.role.is_manager:
        raise exc.NoPermission

    # Check with course role
    if not await is_course_manager(course_id, request.account.id):
        raise exc.NoPermission

    data = await request.json()
    class_id = await db.class_.create(
        name=data['name'],
        course_id=course_id,
        is_enabled=data['is-enabled'],
        is_hidden=data['is-hidden'],
    )

    return {
        'id': class_id,
    }


@router.get('/course/{course_id}/class')
@util.enveloped
async def get_classes_under_course(course_id: int, request: auth.AuthedRequest):
    try:
        await db.course.get_member_role(course_id=course_id, member_id=request.account.id)
    except exc.NotFound:  # Not even in course
        if not request.account.role.is_manager:  # and is not manager
            raise exc.NoPermission

    return await db.course.get_classes_id(course_id=course_id)


@router.get('/class')
@util.enveloped
async def get_classes():
    return [model.pbc109]


@router.get('/class/{class_id}')
@util.enveloped
async def get_class(class_id: int):
    return model.pbc109


@router.patch('/class/{class_id}')
@util.enveloped
async def modify_class(class_id: int):
    pass


@router.delete('/class/{class_id}')
@util.enveloped
async def remove_class(class_id: int):
    pass


@router.get('/class/{class_id}/member')
@util.enveloped
async def get_class_members(class_id: int):
    return [{
        'account': model.account_simple,
        'role': model.ta,
    }]


@router.patch('/class/{class_id}/member')
@util.enveloped
async def modify_class_member(class_id: int):
    pass


@router.delete('/class/{class_id}/member')
@util.enveloped
async def remove_class_member(class_id: int):
    pass


@router.post('/class/{class_id}/team')
@util.enveloped
async def create_team_under_class(class_id: int):
    return {'id': 1}


@router.get('/class/{class_id}/team')
@util.enveloped
async def get_teams_under_class(class_id: int):
    return [model.team_1]


@router.get('/team')
@util.enveloped
async def get_teams():
    return [model.team_1]


@router.get('/team/{team_id}')
@util.enveloped
async def get_team(team_id: int):
    return model.team_1


@router.patch('/team/{team_id}')
@util.enveloped
async def modify_team(team_id: int):
    pass


@router.delete('/team/{team_id}')
@util.enveloped
async def remove_team(team_id: int):
    pass


@router.get('/team/{team_id}/member')
@util.enveloped
async def get_team_members(team_id: int):
    return [{
        'account': model.account_simple,
        'role': {
            'name': 'Leader',
            'level': 'ADMIN',
        },
    }]


@router.patch('/team/{team_id}/member')
@util.enveloped
async def modify_team_member(team_id: int):
    pass


@router.delete('/team/{team_id}/member')
@util.enveloped
async def remove_team_member(team_id: int):
    pass
