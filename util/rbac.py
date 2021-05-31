from base.enum import RoleType
import exceptions as exc
from persistence import database as db


async def validate(account_id: int, min_role: RoleType,
                   class_id: int = None, team_id: int = None, problem_id: int = None, challenge_id: int = None,
                   inherit=True) -> bool:
    """
    Validates if given account owns specific role, possibly of specific group.
    Only one group_id can be given. If multiple are given, upper-level ones will be ignored.

    :param account_id: The account to check with.
    :param min_role: The role to check. Default allows supervise (e.g. manager role is effective if checking normal)
    :param problem_id: If given, check if account owns problem auth by retrieving challenge and class id.
                       If inherit=False, will only check class.
    :param challenge_id: If given, check if account owns challenge auth by retrieving class_id from database.
                         If inherit=False, will only check class.
    :param class_id: If given, check role of class level with class_id.
    :param team_id: If given, check role of team level with team_id.
    :param inherit: If given True (default), inherit role from parent group;
                    if given False, only check role in given group level.
    :return: A boolean value which implies if given role is checked valid or not.
    """
    if problem_id is not None:
        challenge_id = ()  # TODO

    if challenge_id is not None:
        class_id = (await db.challenge.read(challenge_id=challenge_id)).class_id

    if team_id is not None:
        try:
            team_role = await db.rbac.read_team_role_by_account_id(team_id=team_id, account_id=account_id)
            assert team_role >= min_role
        except (exc.NotFound, AssertionError):
            if not inherit:
                return False  # no inherit -> only check for team-level
            # try class role, get class id
            class_id = db.team.read_class_id(team_id=team_id)
        else:
            return True

    if class_id is not None:
        try:
            class_role = await db.rbac.read_class_role_by_account_id(class_id=class_id, account_id=account_id)
            assert class_role >= min_role
        except (exc.NotFound, AssertionError):
            if not inherit:
                return False  # no inherit -> only check for class-level
            # try global role
            pass
        else:
            return True

    try:
        global_role = await db.rbac.read_global_role_by_account_id(account_id=account_id)
        assert global_role >= min_role
    except (exc.NotFound, AssertionError):
        return False
    else:
        return True
