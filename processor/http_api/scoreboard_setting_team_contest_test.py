from datetime import datetime, timedelta
import unittest

from base import enum, do
from util import mock, security
import exceptions as exc

from . import scoreboard_setting_team_contest


class TestViewTeamContestScoreboard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.scoreboard_id = 1
        self.start_time = datetime(2023, 7, 20, 12, 0, 0)
        self.end_time = datetime(2023, 7, 29, 12, 0, 0)

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
        self.scoreboard_project = do.Scoreboard(
            id=2,
            challenge_id=2,
            challenge_label='label2',
            title='title2',
            target_problem_ids=[3, 4],
            is_deleted=False,
            type=enum.ScoreboardType.team_project,
            setting_id=2,
        )
        self.setting_data = do.ScoreboardSettingTeamContest(
            id=1,
            penalty_formula='solved_time_mins + wrong_submissions',
            team_label_filter='filter',
        )
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.end_time,
            selection_type=enum.TaskSelectionType.last,
            title='title',
            setter_id=1,
            description='description',
            start_time=self.start_time,
            end_time=self.end_time,
            is_deleted=False,
        )
        self.teams = [do.Team(
            id=1,
            name='name',
            class_id=1,
            label='label',
            is_deleted=False,
        ), do.Team(
            id=2,
            name='name2',
            class_id=2,
            label='label2',
            is_deleted=False,
        )]
        self.team_problem_datas = {
            1: [
                scoreboard_setting_team_contest.ViewTeamContestScoreboardProblemScoreOutput(
                    problem_id=3,
                    submit_count=1,
                    is_solved=True,
                    solve_time=5,
                    is_first=True,
                    penalty=5,
                    submission_id=1,
                ), scoreboard_setting_team_contest.ViewTeamContestScoreboardProblemScoreOutput(
                    problem_id=4,
                    submit_count=1,
                    is_solved=True,
                    solve_time=5,
                    is_first=True,
                    penalty=5,
                    submission_id=1,
                )],
            2: [
                scoreboard_setting_team_contest.ViewTeamContestScoreboardProblemScoreOutput(
                    problem_id=3,
                    submit_count=1,
                    is_solved=False,
                    solve_time=0,
                    is_first=False,
                    penalty=0,
                    submission_id=2,
                ), scoreboard_setting_team_contest.ViewTeamContestScoreboardProblemScoreOutput(
                    problem_id=4,
                    submit_count=1,
                    is_solved=False,
                    solve_time=0,
                    is_first=False,
                    penalty=0,
                    submission_id=2,
                )]}
        self.verdict = [
            (1, 1, self.start_time+timedelta(minutes=5), enum.VerdictType.accepted),
            (2, 2, self.start_time+timedelta(minutes=10), enum.VerdictType.wrong_answer)
        ]
        self.first_solve_team_id = 1
        self.team_solve_mins = {1: 5}
        self.team_wa_count = {2: 1},
        self.team_submit_count = {1: 1, 2: 1}
        self.team_submission_id = {1: 1, 2: 2}
        self.output = [
            scoreboard_setting_team_contest.ViewTeamContestScoreboardOutput(
                team_id=1,
                team_name='name',
                target_problem_data=self.team_problem_datas[1],
                total_penalty=10,
                solved_problem_count=2,
            ), scoreboard_setting_team_contest.ViewTeamContestScoreboardOutput(
                team_id=2,
                team_name='name2',
                target_problem_data=self.team_problem_datas[2],
                total_penalty=0,
                solved_problem_count=0,
            )]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')
            db_scoreboard_setting_team_contest = controller.mock_module(
                'persistence.database.scoreboard_setting_team_contest',
            )
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_team = controller.mock_module('persistence.database.team')
            db_judgment = controller.mock_module('persistence.database.judgment')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, scoreboard_id=self.scoreboard_id,
            ).returns(True)
            db_scoreboard.async_func('read').call_with(self.scoreboard_id).returns(
                self.scoreboard_contest,
            )

            db_scoreboard_setting_team_contest.async_func('read').call_with(self.scoreboard_contest.setting_id).returns(
                self.setting_data,
            )

            db_challenge.async_func('read').call_with(challenge_id=self.scoreboard_contest.challenge_id).returns(
                self.challenge,
            )
            db_team.async_func('browse_with_team_label_filter').call_with(
                class_id=self.challenge.class_id,
                team_label_filter=self.setting_data.team_label_filter,
            ).returns(self.teams)

            db_challenge.async_func('read').call_with(self.scoreboard_contest.challenge_id).returns(
                self.challenge,
            )

            for problem_id in self.scoreboard_contest.target_problem_ids:

                db_judgment.async_func('get_class_all_team_all_submission_verdict').call_with(
                    problem_id=problem_id, class_id=self.challenge.class_id, team_ids=[team.id for team in self.teams],
                ).returns(self.verdict)

                for team_id in self.team_problem_datas:
                    if team_id in self.team_solve_mins:
                        service_scoreboard.func('calculate_penalty').call_with(
                            formula=self.setting_data.penalty_formula,
                            solved_time_mins=self.team_solve_mins[team_id],
                            wrong_submissions=0,
                        ).returns(5)

            result = await mock.unwrap(scoreboard_setting_team_contest.view_team_contest_scoreboard)(
                scoreboard_id=self.scoreboard_id,
            )

        self.assertEqual(result, self.output)

    async def test_illegal_input(self):
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
            db_scoreboard.async_func('read').call_with(self.scoreboard_id).returns(
                self.scoreboard_project,
            )

            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(scoreboard_setting_team_contest.view_team_contest_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                )

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
                await mock.unwrap(scoreboard_setting_team_contest.view_team_contest_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                )


class TestEditTeamContestScoreboard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.scoreboard_id = 1
        self.input = scoreboard_setting_team_contest.EditScoreboardInput(
            challenge_label='label',
            title='title',
            target_problem_ids=[1, 2],
            penalty_formula='solved_time_mins',
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
            db_scoreboard_setting_team_contest = controller.mock_module(
                'persistence.database.scoreboard_setting_team_contest',
            )
            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(True)

            service_scoreboard.func('validate_penalty_formula').call_with(
                formula=self.input.penalty_formula,
            ).returns(True)

            db_scoreboard_setting_team_contest.async_func('edit_with_scoreboard').call_with(
                scoreboard_id=self.scoreboard_id, challenge_label=self.input.challenge_label, title=self.input.title,
                target_problem_ids=self.input.target_problem_ids, penalty_formula=self.input.penalty_formula,
                team_label_filter=self.input.team_label_filter,
            ).returns(None)

            result = await mock.unwrap(scoreboard_setting_team_contest.edit_team_contest_scoreboard)(
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
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(True)

            service_scoreboard.func('validate_penalty_formula').call_with(
                formula=self.input.penalty_formula,
            ).returns(False)

            with self.assertRaises(exc.InvalidFormula):
                await mock.unwrap(scoreboard_setting_team_contest.edit_team_contest_scoreboard)(
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
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(scoreboard_setting_team_contest.edit_team_contest_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                    data=self.input,
                )
