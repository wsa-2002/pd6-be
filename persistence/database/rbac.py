from base.enum import RoleType
import exceptions

from .base import FetchOne


async def read_system_role_by_account_id(account_id: int) -> RoleType:
    async with FetchOne(
            event='get system role by account id',
            sql=r'SELECT role'
                r'  FROM account'
                r' WHERE id = %(account_id)s',
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_account_id(class_id: int, account_id: int) -> RoleType:
    async with FetchOne(
            event='get class role by account id',
            sql=r'SELECT role'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s'
                r'   AND member_id = %(account_id)s',
            class_id=class_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def any_class_role(member_id: int, role: RoleType) -> bool:
    try:
        async with FetchOne(
                event='',
                sql=r'SELECT *'
                    r'  FROM class_member'
                    r' WHERE member_id = %(member_id)s'
                    r'   AND role = %(role)s',
                member_id=member_id,
                role=role,
        ):
            pass
    except exceptions.persistence.NotFound:
        return False
    else:
        return True


async def read_team_role_by_account_id(team_id: int, account_id: int) -> RoleType:
    async with FetchOne(
            event='get team role by account id',
            sql=r'SELECT role'
                r'  FROM team_member'
                r' WHERE team_id = %(team_id)s'
                r'   AND member_id = %(account_id)s',
            team_id=team_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_team_account_id(team_id: int, account_id: int,
                                             include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by team account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN team'
                fr'         ON class_member.class_id = team.class_id'
                fr'        AND team.id = %(team_id)s'
                fr'{"      AND NOT team.is_deleted" if not include_deleted else ""}'
                fr' WHERE member_id = %(account_id)s',
            team_id=team_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_challenge_account_id(challenge_id: int, account_id: int,
                                                  include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by challenge account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'        AND challenge.id = %(challenge_id)s'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' WHERE member_id = %(account_id)s',
            challenge_id=challenge_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_problem_account_id(problem_id: int, account_id: int,
                                                include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by problem account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN problem'
                fr'         ON challenge.id = problem.challenge_id'
                fr'{"      AND NOT problem.is_deleted" if not include_deleted else ""}'
                fr'        AND problem.id = %(problem_id)s'
                fr' WHERE member_id = %(account_id)s',
            problem_id=problem_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_testcase_account_id(testcase_id: int, account_id: int,
                                                 include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by testcase account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN problem'
                fr'         ON challenge.id = problem.challenge_id'
                fr'{"      AND NOT problem.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN testcase'
                fr'         ON problem.id = testcase.problem_id'
                fr'{"      AND NOT testcase.is_deleted" if not include_deleted else ""}'
                fr'        AND testcase.id = %(testcase_id)s'
                fr' WHERE member_id = %(account_id)s',
            testcase_id=testcase_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_assisting_data_account_id(assisting_data_id: int, account_id: int,
                                                       include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by assisting_data account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN problem'
                fr'         ON challenge.id = problem.challenge_id'
                fr'{"      AND NOT problem.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN assisting_data'
                fr'         ON problem.id = assisting_data.problem_id'
                fr'{"      AND NOT assisting_data.is_deleted" if not include_deleted else ""}'
                fr'        AND assisting_data.id = %(assisting_data_id)s'
                fr' WHERE member_id = %(account_id)s',
            assisting_data_id=assisting_data_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_submission_account_id(submission_id: int, account_id: int,
                                                   include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by submission account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN problem'
                fr'         ON challenge.id = problem.challenge_id'
                fr'{"      AND NOT problem.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN submission'
                fr'         ON problem.id = submission.problem_id'
                fr'        AND submission.id = %(submission_id)s'
                fr' WHERE member_id = %(account_id)s',
            submission_id=submission_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_essay_account_id(essay_id: int, account_id: int,
                                              include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by essay account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN essay'
                fr'         ON challenge.id = essay.challenge_id'
                fr'{"      AND NOT essay.is_deleted" if not include_deleted else ""}'
                fr'        AND essay.id = %(essay_id)s'
                fr' WHERE member_id = %(account_id)s',
            essay_id=essay_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_essay_submission_account_id(essay_submission_id: int, account_id: int,
                                                         include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by essay_submission account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN essay'
                fr'         ON challenge.id = essay.challenge_id'
                fr'{"      AND NOT essay.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN essay_submission'
                fr'         ON essay.id = essay_submission.essay_id'
                fr'        AND essay_submission.id = %(essay_submission_id)s'
                fr' WHERE member_id = %(account_id)s',
            essay_submission_id=essay_submission_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_peer_review_account_id(peer_review_id: int, account_id: int,
                                                    include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by peer_review account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN peer_review'
                fr'         ON challenge.id = peer_review.challenge_id'
                fr'{"      AND NOT peer_review.is_deleted" if not include_deleted else ""}'
                fr'        AND peer_review.id = %(peer_review_id)s'
                fr' WHERE member_id = %(account_id)s',
            peer_review_id=peer_review_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_peer_review_record_account_id(peer_review_record_id: int, account_id: int,
                                                           include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by peer_review_record account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN peer_review'
                fr'         ON challenge.id = peer_review.challenge_id'
                fr'{"      AND NOT peer_review.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN peer_review_record'
                fr'         ON peer_review.id = peer_review_record.peer_review_id'
                fr'        AND peer_review_record.id = %(peer_review_record_id)s'
                fr' WHERE member_id = %(account_id)s',
            peer_review_record_id=peer_review_record_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_scoreboard_account_id(scoreboard_id: int, account_id: int,
                                                   include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by scoreboard account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN scoreboard'
                fr'         ON challenge.id = scoreboard.challenge_id'
                fr'{"      AND NOT scoreboard.is_deleted" if not include_deleted else ""}'
                fr'        AND scoreboard.id = %(scoreboard_id)s'
                fr' WHERE member_id = %(account_id)s',
            scoreboard_id=scoreboard_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_scoreboard_setting_team_project_account_id(
        scoreboard_setting_team_project_id: int, account_id: int,
        include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by scoreboard_setting_team_project account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN challenge'
                fr'         ON class_member.class_id = challenge.class_id'
                fr'{"      AND NOT challenge.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN scoreboard'
                fr'         ON challenge.id = scoreboard.challenge_id'
                fr'{"      AND NOT scoreboard.is_deleted" if not include_deleted else ""}'
                fr' INNER JOIN scoreboard_setting_team_project'
                fr'         ON scoreboard.setting_id = scoreboard_setting_team_project.id'
                fr'        AND scoreboard_setting_team_project = %(scoreboard_setting_team_project_id)s'
                fr' WHERE member_id = %(account_id)s',
            scoreboard_setting_team_project_id=scoreboard_setting_team_project_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)


async def read_class_role_by_grade_account_id(grade_id: int, account_id: int,
                                              include_deleted=False) -> RoleType:
    async with FetchOne(
            event='get class role by grade account id',
            sql=fr'SELECT role'
                fr'  FROM class_member'
                fr' INNER JOIN grade'
                fr'         ON class_member.class_id = grade.class_id'
                fr'        AND grade.id = %(grade_id)s'
                fr'{"      AND NOT grade.is_deleted" if not include_deleted else ""}'
                fr' WHERE member_id = %(account_id)s',
            grade_id=grade_id,
            account_id=account_id,
    ) as (role,):
        return RoleType(role)
