from base.enum import RoleType
import exceptions as exc
from persistence import database as db


async def validate(account_id: int, min_role: RoleType,
                   class_id: int = None, team_id: int = None):
    if team_id is not None:
        try:
            team_role = await db.rbac.get_team_role_by_account_id(team_id=team_id, account_id=account_id)
            assert team_role >= min_role
        except (exc.NotFound, AssertionError):
            # try class role, get class id
            class_id = db.team.get_class_id(team_id=team_id)
        else:
            return

    if class_id is not None:
        try:
            class_role = await db.rbac.get_class_role_by_account_id(class_id=class_id, account_id=account_id)
            assert class_role >= min_role
        except (exc.NotFound, AssertionError):
            # try global role
            pass
        else:
            return

    try:
        global_role = await db.rbac.get_global_role_by_account_id(account_id=account_id)
        assert global_role >= min_role
    except (exc.NotFound, AssertionError):
        raise exc.NoPermission
    else:
        return
