from datetime import datetime, timedelta
import time
import unittest

from base import enum, do
from util import mock, security
import exceptions as exc

from . import hardcode


class TestViewTeamContestScoreboardRuns(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:

        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.time = datetime(2023, 8, 1, 1, 1, 1)
        self.now = self.time + timedelta(seconds=30)
        self.scoreboard_id = 1

        self.scoreboard = do.Scoreboard(
            id=1,
            challenge_id=1,
            challenge_label='label',
            title='title',
            target_problem_ids=[1],
            is_deleted=False,
            type=enum.ScoreboardType.team_contest,
            setting_id=1,
        )
        self.illegal_scoreboard = do.Scoreboard(
            id=1,
            challenge_id=1,
            challenge_label='label',
            title='title',
            target_problem_ids=[1],
            is_deleted=False,
            type=enum.ScoreboardType.team_project,
            setting_id=1,
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
            start_time=self.time,
            end_time=self.time + timedelta(seconds=5),
            is_deleted=False,
        )
        self.teams = [
            do.Team(
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
            ),
        ]
        self.freeze_result = [
            (1, 1, self.time + timedelta(minutes=5), enum.VerdictType.accepted),
            (2, 2, self.time + timedelta(minutes=10), enum.VerdictType.accepted),
        ]
        self.problem_run_infos = [
            hardcode.EachRun(
                team=1,
                problem=1,
                result="Yes",
                submissionTime=5,
            ),
            hardcode.EachRun(
                team=2,
                problem=1,
                result="Yes",
                submissionTime=10,
            ),
        ]
        self.result = hardcode.ViewTeamContestScoreboardRunsOutput(
            time=hardcode.TimeInfo(
                contestTime=5,
                noMoreUpdate=True,
                timestamp=30,
            ),
            runs=[
                hardcode.ReturnEachRun(
                    id=0,
                    team=1,
                    problem=1,
                    result="Yes",
                    submissionTime=5,
                ), hardcode.ReturnEachRun(
                    id=1,
                    team=2,
                    problem=1,
                    result="Yes",
                    submissionTime=10,
                ),
            ]
        )

    # for cache
    def tearDown(self):
        time.sleep(1.1)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.time)

            service_rbac = controller.mock_module('service.rbac')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')
            db_scoreboard_setting_team_contest = controller.mock_module(
                'persistence.database.scoreboard_setting_team_contest',
            )
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_team = controller.mock_module('persistence.database.team')
            db_judgment = controller.mock_module('persistence.database.judgment')
            datetime_now = controller.mock_module('datetime.datetime').func('now')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal,
                scoreboard_id=self.scoreboard_id,
            ).returns(True)

            db_scoreboard.async_func('read').call_with(self.scoreboard_id).returns(self.scoreboard)

            db_scoreboard_setting_team_contest.async_func('read').call_with(self.scoreboard.setting_id).returns(
                self.setting_data,
            )

            db_challenge.async_func('read').call_with(
                challenge_id=self.scoreboard.challenge_id,
            ).returns(self.challenge)
            db_team.async_func('browse_with_team_label_filter').call_with(
                class_id=self.challenge.class_id,
                team_label_filter=self.setting_data.team_label_filter,
            ).returns(self.teams)

            db_challenge.async_func('read').call_with(
                self.scoreboard.challenge_id,
            ).returns(self.challenge)

            db_judgment.async_func('get_class_all_team_submission_verdict_before_freeze').call_with(
                problem_id=self.scoreboard.target_problem_ids[0],
                class_id=self.challenge.class_id,
                team_ids=[1, 2],
                freeze_time=self.challenge.end_time - timedelta(hours=1),
            ).returns(self.freeze_result)

            # for noMoreUpdate in TimeInfo
            datetime_now.call_with().returns(self.now)
            # for timeStamp in TimeInfo
            datetime_now.call_with().returns(self.now)

            result = await mock.unwrap(hardcode.view_team_contest_scoreboard_runs)(self.scoreboard_id)

        self.assertEqual(result, self.result)

    async def test_illegal_input(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.time)

            service_rbac = controller.mock_module('service.rbac')
            db_scoreboard = controller.mock_module('persistence.database.scoreboard')

            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal,
                scoreboard_id=self.scoreboard_id,
            ).returns(True)

            db_scoreboard.async_func('read').call_with(self.scoreboard_id).returns(self.illegal_scoreboard)

            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(hardcode.view_team_contest_scoreboard_runs)(self.scoreboard_id)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)
            context.set_request_time(self.time)

            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_class').call_with(
                self.login_account.id, enum.RoleType.normal,
                scoreboard_id=self.scoreboard_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(hardcode.view_team_contest_scoreboard_runs)(self.scoreboard_id)


