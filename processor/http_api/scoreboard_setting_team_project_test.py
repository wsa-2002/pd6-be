from datetime import datetime

import unittest

from base import enum, do
from util import mock, security
import exceptions as exc

from . import scoreboard_setting_team_project


class TestEditTeamProjectScoreboard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.scoreboard_id = 1
        self.input = scoreboard_setting_team_project.EditScoreboardInput(
            challenge_label='label',
            title='title',
            target_problem_ids=[1, 2],
            scoring_formula='formula',
            baseline_team_id=1,
            rank_by_total_score=True,
            team_label_filter='filter',
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')
            db_scoreboard_setting_team_project = controller.mock_module(
                'persistence.database.scoreboard_setting_team_project'
            )

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id
            ).returns(True)

            service_scoreboard.async_func('validate_formula').call_with(
                formula=self.input.scoring_formula
            ).returns(True)

            db_scoreboard_setting_team_project.async_func('edit_with_scoreboard').call_with(
                scoreboard_id=self.scoreboard_id, challenge_label=self.input.challenge_label, title=self.input.title,
                target_problem_ids=self.input.target_problem_ids, scoring_formula=self.input.scoring_formula,
                baseline_team_id=self.input.baseline_team_id, rank_by_total_score=self.input.rank_by_total_score,
                team_label_filter=self.input.team_label_filter,
            ).returns(None)

            result = await mock.unwrap(scoreboard_setting_team_project.edit_team_project_scoreboard)(
                scoreboard_id=self.scoreboard_id,
                data=self.input,
            )

        self.assertIsNone(result)

    async def test_invalid_formula(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id
            ).returns(True)

            service_scoreboard.async_func('validate_formula').call_with(
                formula=self.input.scoring_formula
            ).returns(False)

            with self.assertRaises(exc.InvalidFormula):
                await mock.unwrap(scoreboard_setting_team_project.edit_team_project_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                    data=self.input,
                )

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(scoreboard_setting_team_project.edit_team_project_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                    data=self.input,
                )

