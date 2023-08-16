from datetime import datetime
import unittest
from uuid import UUID

from base import enum, do
from util import mock, security
import exceptions as exc

from . import scoreboard_setting_team_project


class TestViewTeamProjectScoreboard(unittest.IsolatedAsyncioTestCase):
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
        self.setting_data = do.ScoreboardSettingTeamProject(
            id=1,
            scoring_formula='class_max + class_min + baseline',
            baseline_team_id=1,
            rank_by_total_score=True,
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
        self.team_problem_scores = {
            1: [scoreboard_setting_team_project.ViewTeamProjectScoreboardProblemScoreOutput(
                    problem_id=3,
                    score=240,
                    submission_id=1,
                ),
                scoreboard_setting_team_project.ViewTeamProjectScoreboardProblemScoreOutput(
                    problem_id=4,
                    score=240,
                    submission_id=1,
                )],
            2: [scoreboard_setting_team_project.ViewTeamProjectScoreboardProblemScoreOutput(
                    problem_id=3,
                    score=240,
                    submission_id=2,
                ),
                scoreboard_setting_team_project.ViewTeamProjectScoreboardProblemScoreOutput(
                    problem_id=4,
                    score=240,
                    submission_id=2,
                )]
        }
        self.team_submission = {1: 1, 2: 2}
        self.team_judgments = {1: 1, 2: 2}
        self.testcase = [do.Testcase(
            id=1,
            problem_id=1,
            is_sample=True,
            score=10,
            label='label',
            input_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            output_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            input_filename='input',
            output_filename='output',
            note='note',
            time_limit=10,
            memory_limit=10,
            is_disabled=True,
            is_deleted=False,
        ), do.Testcase(
            id=2,
            problem_id=1,
            is_sample=False,
            score=10,
            label='label',
            input_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            output_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            input_filename='input',
            output_filename='output',
            note='note',
            time_limit=10,
            memory_limit=10,
            is_disabled=True,
            is_deleted=False,
        )]
        self.judge_id_judge_case = {
            1: do.JudgeCase(judgment_id=1, testcase_id=1, verdict=enum.VerdictType.accepted,
                            time_lapse=1, peak_memory=1, score=10),
            2: do.JudgeCase(judgment_id=2, testcase_id=2, verdict=enum.VerdictType.accepted,
                            time_lapse=1, peak_memory=1, score=20),
        }

        self.teams_score = {1: 60, 2: 80}
        self.output = [
            scoreboard_setting_team_project.ViewTeamProjectScoreboardOutput(
                team_id=1,
                team_name='name',
                target_problem_data=self.team_problem_scores[1],
                total_score=480
                if self.setting_data.rank_by_total_score else None,
            ),
            scoreboard_setting_team_project.ViewTeamProjectScoreboardOutput(
                team_id=2,
                team_name='name2',
                target_problem_data=self.team_problem_scores[2],
                total_score=480
                if self.setting_data.rank_by_total_score else None,
            ),
        ]

    def mock_calculator(self, _):
        return eval(self.setting_data.scoring_formula, {
            'class_max': 100,
            'class_min': 60,
            'baseline': 80,
        })

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_scoreboard = controller.mock_module('service.scoreboard')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')
            db_scoreboard_setting_team_project = controller.mock_module(
                'persistence.database.scoreboard_setting_team_project',
            )
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_team = controller.mock_module('persistence.database.team')
            db_judgment = controller.mock_module('persistence.database.judgment')
            db_testcase = controller.mock_module('persistence.database.testcase')
            db_judge_case = controller.mock_module('persistence.database.judge_case')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal, scoreboard_id=self.scoreboard_id,
            ).returns(True)
            db_scoreboard.async_func('read').call_with(self.scoreboard_id).returns(
                self.scoreboard_project,
            )

            db_scoreboard_setting_team_project.async_func('read').call_with(self.scoreboard_contest.setting_id).returns(
                self.setting_data,
            )

            db_challenge.async_func('read').call_with(challenge_id=self.scoreboard_contest.challenge_id).returns(
                self.challenge,
            )
            db_team.async_func('browse_with_team_label_filter').call_with(
                class_id=self.challenge.class_id,
                team_label_filter=self.setting_data.team_label_filter,
            ).returns(self.teams)

            for problem_id in self.scoreboard_project.target_problem_ids:

                db_judgment.async_func('get_class_last_team_submission_judgment').call_with(
                    problem_id=problem_id, class_id=self.challenge.class_id, team_ids=[team.id for team in self.teams],
                ).returns((self.team_submission, self.team_judgments))

                db_testcase.async_func('browse').call_with(problem_id=problem_id).returns(
                    self.testcase,
                )
                for testcase in self.testcase:
                    if testcase.is_sample:
                        continue

                    db_judge_case.async_func('batch_get_with_judgment').call_with(
                        testcase_id=testcase.id,
                        judgment_ids=mock.AnySetOfValues(self.team_judgments.values()),
                        verdict=enum.VerdictType.accepted,
                    ).returns(self.judge_id_judge_case)

                    service_scoreboard.func('get_team_project_calculator').call_with(
                        formula=self.setting_data.scoring_formula,
                        class_max=20,
                        class_min=10,
                        baseline=10,
                    ).returns(self.mock_calculator)

            result = await mock.unwrap(scoreboard_setting_team_project.view_team_project_scoreboard)(
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
                self.scoreboard_contest,
            )

            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(scoreboard_setting_team_project.view_team_project_scoreboard)(
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
                await mock.unwrap(scoreboard_setting_team_project.view_team_project_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                )


class TestEditTeamProjectScoreboard(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.scoreboard_id = 1
        self.input = scoreboard_setting_team_project.EditScoreboardInput(
            challenge_label='label',
            title='title',
            target_problem_ids=[1, 2],
            scoring_formula='class_max + class_min + baseline',
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
            db_scoreboard_setting_team_project = controller.mock_module(
                'persistence.database.scoreboard_setting_team_project',
            )
            service_scoreboard = controller.mock_module('service.scoreboard')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(True)

            service_scoreboard.async_func('validate_formula').call_with(
                formula=self.input.scoring_formula,
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
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(True)

            service_scoreboard.async_func('validate_formula').call_with(
                formula=self.input.scoring_formula,
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
                self.login_account.id, enum.RoleType.manager, scoreboard_id=self.scoreboard_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(scoreboard_setting_team_project.edit_team_project_scoreboard)(
                    scoreboard_id=self.scoreboard_id,
                    data=self.input,
                )
