from functools import partial
from typing import Optional

from base.enum import RoleType
import exceptions as exc
import log
from persistence import database as db


async def validate_inherit(account_id: int, min_role: RoleType, *,
                           class_id: int = None, team_id: int = None) -> bool:
    """
    Validates if given account owns specific role, possibly of specific group.
    Only one group_id can be given. If multiple are given, upper-level ones will be ignored.
    Inheritance is allowed.

    :param account_id: The account to check with.
    :param min_role: The role to check. Default allows supervise (e.g. manager role is effective if checking normal)
    :param class_id: If given, check role of class level with class_id.
    :param team_id: If given, check role of team level with team_id.
    :return: A boolean value which implies if given role is checked valid or not.
    """
    log.info(f"Validating inherited role for {account_id=}, {min_role=}")

    if team_id is not None:
        log.info("Check for team role...")
        try:
            team_role = await db.rbac.read_team_role_by_account_id(team_id=team_id, account_id=account_id)
            log.info(f"Retrieved {team_role=}")
            if team_role < min_role:
                raise PermissionError
        except (exc.persistence.NotFound, PermissionError):
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
            # try global role
            log.info("Class role not satisfied, move on to global role")
        else:
            log.info("Class role verified")
            return True

    try:
        log.info("Check for global role...")
        global_role = await db.rbac.read_system_role_by_account_id(account_id=account_id)
        if global_role < min_role:
            raise PermissionError
    except (exc.persistence.NotFound, PermissionError):
        log.info("Global role not satisfied, check fail")
        return False
    else:
        log.info("Global role verified")
        return True


async def get_system_role(account_id: int) -> Optional[RoleType]:
    log.info("Get system role...")
    try:
        return await db.rbac.read_system_role_by_account_id(account_id=account_id)
    except exc.persistence.NotFound:
        return None


async def validate_system(account_id: int, min_role: RoleType) -> bool:
    log.info(f"Validating system role for {account_id=}, {min_role=}")

    try:
        system_role = await get_system_role(account_id)
    except exc.persistence.NotFound:
        return False
    else:
        return system_role >= min_role


async def get_class_role(account_id: int, *,
                         class_id: int = None, team_id: int = None,
                         challenge_id: int = None, problem_id: int = None,
                         testcase_id: int = None, assisting_data_id: int = None,
                         submission_id: int = None,
                         peer_review_id: int = None, peer_review_record_id: int = None,
                         scoreboard_id: int = None, scoreboard_setting_team_project_id: int = None,
                         essay_id: int = None, essay_submission_id: int = None,
                         grade_id: int = None) -> Optional[RoleType]:
    log.info("Get class role...")

    if class_id:
        read_role = partial(db.rbac.read_class_role_by_account_id, class_id=class_id)
    elif team_id:
        read_role = partial(db.rbac.read_class_role_by_team_account_id, team_id=team_id)
    elif challenge_id:
        read_role = partial(db.rbac.read_class_role_by_challenge_account_id, challenge_id=challenge_id)
    elif problem_id:
        read_role = partial(db.rbac.read_class_role_by_problem_account_id, problem_id=problem_id)
    elif testcase_id:
        read_role = partial(db.rbac.read_class_role_by_testcase_account_id, testcase_id=testcase_id)
    elif assisting_data_id:
        read_role = partial(db.rbac.read_class_role_by_assisting_data_account_id, assisting_data_id=assisting_data_id)
    elif submission_id:
        read_role = partial(db.rbac.read_class_role_by_submission_account_id, submission_id=submission_id)
    elif peer_review_id:
        read_role = partial(db.rbac.read_class_role_by_peer_review_account_id, peer_review_id=peer_review_id)
    elif peer_review_record_id:
        read_role = partial(db.rbac.read_class_role_by_peer_review_record_account_id,
                            peer_review_record_id=peer_review_record_id)
    elif scoreboard_id:
        read_role = partial(db.rbac.read_class_role_by_scoreboard_account_id, scoreboard_id=scoreboard_id)
    elif scoreboard_setting_team_project_id:
        read_role = partial(db.rbac.read_class_role_by_scoreboard_setting_team_project_account_id,
                            scoreboard_setting_team_project_id=scoreboard_setting_team_project_id)
    elif essay_id:
        read_role = partial(db.rbac.read_class_role_by_essay_account_id, essay_id=essay_id)
    elif essay_submission_id:
        read_role = partial(db.rbac.read_class_role_by_essay_submission_account_id,
                            essay_submission_id=essay_submission_id)
    elif grade_id:
        read_role = partial(db.rbac.read_class_role_by_grade_account_id, grade_id=grade_id)
    else:
        raise ValueError

    try:
        return await read_role(account_id=account_id)
    except exc.persistence.NotFound:
        return None


async def validate_class(account_id: int, min_role: RoleType, *,
                         class_id: int = None, team_id: int = None,
                         challenge_id: int = None, problem_id: int = None,
                         testcase_id: int = None, assisting_data_id: int = None,
                         submission_id: int = None,
                         peer_review_id: int = None, peer_review_record_id: int = None,
                         scoreboard_id: int = None, scoreboard_setting_team_project_id: int = None,
                         essay_id: int = None, essay_submission_id: int = None,
                         grade_id: int = None) -> bool:
    log.info(f"Validating class role for {account_id=}, {min_role=}")

    try:
        class_role = await get_class_role(
            account_id,
            class_id=class_id, team_id=team_id,
            challenge_id=challenge_id, problem_id=problem_id,
            testcase_id=testcase_id, assisting_data_id=assisting_data_id,
            submission_id=submission_id,
            peer_review_id=peer_review_id, peer_review_record_id=peer_review_record_id,
            scoreboard_id=scoreboard_id, scoreboard_setting_team_project_id=scoreboard_setting_team_project_id,
            essay_id=essay_id, essay_submission_id=essay_submission_id,
            grade_id=grade_id,
        )
    except exc.persistence.NotFound:
        return False
    else:
        return class_role >= min_role


async def get_team_role(account_id: int, *,
                        team_id: int = None,
                        ) -> Optional[RoleType]:
    log.info("Get team role...")

    if team_id:
        read_role = partial(db.rbac.read_team_role_by_account_id, team_id=team_id)
    else:
        raise ValueError

    try:
        return await read_role(account_id=account_id)
    except exc.persistence.NotFound:
        return None


async def validate_team(account_id: int, min_role: RoleType, *,
                        team_id: int = None) -> bool:
    log.info(f"Validating team role for {account_id=}, {min_role=}")

    try:
        team_role = await get_team_role(
            account_id,
            team_id=team_id,
        )
    except exc.persistence.NotFound:
        return False
    else:
        return team_role >= min_role
