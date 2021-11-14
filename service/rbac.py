from typing import Optional

from base.enum import RoleType
import exceptions as exc
import log
from persistence import database as db


async def get_role(account_id: int, *, class_id: int = None, team_id: int = None) -> Optional[RoleType]:
    if team_id is not None:
        log.info("Get team role...")
        try:
            return await db.rbac.read_team_role_by_account_id(team_id=team_id, account_id=account_id)
        except exc.persistence.NotFound:
            return None

    if class_id is not None:
        log.info("Get class role...")
        try:
            return await db.rbac.read_class_role_by_account_id(class_id=class_id, account_id=account_id)
        except exc.persistence.NotFound:
            return None

    log.info("Get global role...")
    try:
        return await db.rbac.read_global_role_by_account_id(account_id=account_id)
    except exc.persistence.NotFound:
        return None


async def validate(account_id: int, min_role: RoleType, *,
                   class_id: int = None, team_id: int = None, inherit: bool = False) -> bool:
    """
    Validates if given account owns specific role, possibly of specific group.
    Only one group_id can be given. If multiple are given, upper-level ones will be ignored.

    :param account_id: The account to check with.
    :param min_role: The role to check. Default allows supervise (e.g. manager role is effective if checking normal)
    :param class_id: If given, check role of class level with class_id.
    :param team_id: If given, check role of team level with team_id.
    :param inherit: If given True (default), inherit role from parent group;
                    if given False, only check role in given group level.
    :return: A boolean value which implies if given role is checked valid or not.
    """
    log.info(f"Validating role for {account_id=}, {min_role=}")

    if team_id is not None:
        log.info("Check for team role...")
        try:
            team_role = await db.rbac.read_team_role_by_account_id(team_id=team_id, account_id=account_id)
            log.info(f"Retrieved {team_role=}")
            if team_role < min_role:
                raise PermissionError
        except (exc.persistence.NotFound, PermissionError):
            if not inherit:
                log.info("Team role not satisfied, check fail")
                return False  # no inherit -> only check for team-level
            # try class role, get class id
            log.info("Team role not satisfied, move on to class role")
            class_id = (await db.team.read(team_id=team_id)).class_id
        else:
            log.info("Team role verified")
            return True

    if class_id is not None:
        log.info("Check for class role...")
        try:
            class_role = await db.rbac.read_class_role_by_account_id(class_id=class_id, account_id=account_id)
            log.info(f"Retrieved {class_role=}")
            if class_role < min_role:
                raise PermissionError
        except (exc.persistence.NotFound, PermissionError):
            if not inherit:
                log.info("Class role not satisfied, check fail")
                return False  # no inherit -> only check for class-level
            # try global role
            log.info("Class role not satisfied, move on to global role")
        else:
            log.info("Class role verified")
            return True

    try:
        log.info("Check for global role...")
        global_role = await db.rbac.read_global_role_by_account_id(account_id=account_id)
        if global_role < min_role:
            raise PermissionError
    except (exc.persistence.NotFound, PermissionError):
        log.info("Global role not satisfied, check fail")
        return False
    else:
        log.info("Global role verified")
        return True

#
# async def get_class_role_from(account_id: int, *, class_id: int, team_id: int,) -> Optional[RoleType]:
#     if class_id:
#         try:
#             return await db.rbac.read_class_role_by_account_id(class_id=class_id, account_id=account_id)
#         except exc.persistence.NotFound:
#             return None
#
#     if team_id:
#         try:
#             return await db.rbac.read_
