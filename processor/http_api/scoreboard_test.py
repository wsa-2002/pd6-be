import unittest

from base import enum, do
from util import mock, security
import exceptions as exc

from . import scoreboard


class TestReadScoreboard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.scoreboard_id = 1

        self.scoreboard_project = do.Scoreboard(
            id=1,
            challenge_id=1,
            challenge_label='label',
            title='title',
            target_problem_ids=[1, 2],
            is_deleted=False,
            type=enum.ScoreboardType.team_project,
            setting_id=1,
        )
        self.output_project = scoreboard.ReadScoreboardOutput(
            id=self.scoreboard_project.id,
            challenge_id=self.scoreboard_project.challenge_id,
            challenge_label=self.scoreboard_project.challenge_label,
            title=self.scoreboard_project.title,
            target_problem_ids=self.scoreboard_project.target_problem_ids,
            is_deleted=self.scoreboard_project.is_deleted,
            type=self.scoreboard_project.type,
            data=do.ScoreboardSettingTeamProject(
                id=1,
                scoring_formula='formula',
                baseline_team_id=1,
                rank_by_total_score=True,
                team_label_filter='filter',
            ),
        )
        self.scoreboard_contest = do.Scoreboard(
            id=2,
            challenge_id=2,
            challenge_label='label2',
            title='title2',
            target_problem_ids=[3, 4],
            is_deleted=False,
            type=enum.ScoreboardType.team_contest,
            setting_id=2,
        )
        self.output_contest = scoreboard.ReadScoreboardOutput(
            id=self.scoreboard_contest.id,
            challenge_id=self.scoreboard_contest.challenge_id,
            challenge_label=self.scoreboard_contest.challenge_label,
            title=self.scoreboard_contest.title,
            target_problem_ids=self.scoreboard_contest.target_problem_ids,
            is_deleted=self.scoreboard_contest.is_deleted,
            type=self.scoreboard_contest.type,
            data=do.ScoreboardSettingTeamContest(
                id=1,
                penalty_formula='formula',
                team_label_filter='filter',
            ),
        )
        self.scoreboard_system_exception = do.Scoreboard(
            id=2,
            challenge_id=2,
            challenge_label='label2',
            title='title2',
            target_problem_ids=[3, 4],
            is_deleted=False,
            type=None,
            setting_id=2,
        )

    async def test_happy_flow_project(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')
            db_scoreboard_setting_team_project = controller.mock_module(
                'persistence.database.scoreboard_setting_team_project',
            )

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, scoreboard_id=self.scoreboard_id
            ).returns(True)
            db_scoreboard.async_func('read').call_with(scoreboard_id=self.scoreboard_id).returns(
                self.scoreboard_project,
            )
            db_scoreboard_setting_team_project.async_func('read').call_with(self.scoreboard_project.setting_id).returns(
                self.output_project.data,
            )

            result = await mock.unwrap(scoreboard.read_scoreboard)(scoreboard_id=self.scoreboard_id)

        self.assertEqual(result, self.output_project)

    async def test_happy_flow_contest(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')
            db_scoreboard_setting_team_contest = controller.mock_module(
                'persistence.database.scoreboard_setting_team_contest',
            )

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, scoreboard_id=self.scoreboard_id,
            ).returns(True)
            db_scoreboard.async_func('read').call_with(scoreboard_id=self.scoreboard_id).returns(
                self.scoreboard_contest,
            )
            db_scoreboard_setting_team_contest.async_func('read').call_with(self.scoreboard_contest.setting_id).returns(
                self.output_contest.data,
            )

            result = await mock.unwrap(scoreboard.read_scoreboard)(scoreboard_id=self.scoreboard_id)

        self.assertEqual(result, self.output_contest)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, scoreboard_id=self.scoreboard_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(scoreboard.read_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                )

    async def test_system_exception(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, scoreboard_id=self.scoreboard_id,
            ).returns(True)
            db_scoreboard.async_func('read').call_with(scoreboard_id=self.scoreboard_id).returns(
                self.scoreboard_system_exception,
            )

            with self.assertRaises(exc.SystemException):
                await mock.unwrap(scoreboard.read_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                )


class TestDeleteScoreboard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.scoreboard_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(True)

            db_scoreboard.async_func('delete').call_with(scoreboard_id=self.scoreboard_id).returns(None)

            result = await mock.unwrap(scoreboard.delete_scoreboard)(scoreboard_id=self.scoreboard_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(scoreboard.delete_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                )
