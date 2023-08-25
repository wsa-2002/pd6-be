from datetime import datetime
import unittest
from uuid import UUID

from base import do, enum
from util import mock

from . import statistics


class TestGetChallengeStatistics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.challenge_id = 1
        self.problems = [
            do.Problem(
                id=1,
                challenge_id=1,
                challenge_label='label',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            ),
            do.Problem(
                id=2,
                challenge_id=1,
                challenge_label='label2',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title2',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            )
        ]

        self.expected_happy_flow_result = [
            (self.problems[0].challenge_label, 1, 1, 1),
            (self.problems[1].challenge_label, 1, 1, 1),
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_problem = controller.mock_module('persistence.database.problem')
            db_problem.async_func('browse_by_challenge').call_with(
                self.challenge_id,
            ).returns(self.problems)
            db_problem.async_func('class_total_ac_member_count').call_with(
                problem_id=self.problems[0].id,
            ).returns(1)
            db_problem.async_func('class_total_submission_count').call_with(
                problem_id=self.problems[0].id, challenge_id=self.challenge_id,
            ).returns(1)
            db_problem.async_func('class_total_member_count').call_with(
                problem_id=self.problems[0].id,
            ).returns(1)
            db_problem.async_func('class_total_ac_member_count').call_with(
                problem_id=self.problems[1].id,
            ).returns(1)
            db_problem.async_func('class_total_submission_count').call_with(
                problem_id=self.problems[1].id, challenge_id=self.challenge_id,
            ).returns(1)
            db_problem.async_func('class_total_member_count').call_with(
                problem_id=self.problems[1].id,
            ).returns(1)

            result = await statistics.get_challenge_statistics(self.challenge_id)

        self.assertEqual(result, self.expected_happy_flow_result)


class TestGetMemberSubmissionStatistics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.challenge_id = 1
        self.challenge = do.Challenge(
            id=1,
            class_id=1,
            publicize_type=enum.ChallengePublicizeType.start_time,
            selection_type=enum.TaskSelectionType.best,
            title='title',
            setter_id=1,
            description='desc',
            start_time=datetime(2023, 7, 29),
            end_time=datetime(2023, 7, 30),
            is_deleted=False,
        )
        self.class_members = [
            do.ClassMember(
                member_id=1,
                class_id=1,
                role=enum.RoleType.normal,
            ),
            do.ClassMember(
                member_id=2,
                class_id=1,
                role=enum.RoleType.normal,
            ),
            do.ClassMember(
                member_id=3,
                class_id=1,
                role=enum.RoleType.guest,
            ),
            do.ClassMember(
                member_id=4,
                class_id=1,
                role=enum.RoleType.manager,
            ),
        ]
        self.problems = [
            do.Problem(
                id=1,
                challenge_id=1,
                challenge_label='label',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            ),
            do.Problem(
                id=2,
                challenge_id=1,
                challenge_label='label2',
                judge_type=enum.ProblemJudgeType.normal,
                setting_id=None,
                title='title2',
                setter_id=1,
                full_score=100,
                description='desc',
                io_description='io_desc',
                source='src',
                hint='hint',
                is_lazy_judge=False,
                is_deleted=False,
                reviser_settings=[],
            )
        ]
        self.essays = [
            do.Essay(
                id=1,
                challenge_id=1,
                challenge_label="challenge",
                title="title",
                setter_id=1,
                description="desc",
                is_deleted=False,
            ),
            do.Essay(
                id=2,
                challenge_id=1,
                challenge_label="challenge",
                title="title",
                setter_id=1,
                description="desc",
                is_deleted=False,
            )
        ]

        self.problem_to_member_judgments = {
            self.problems[0].id: {1: do.Judgment(
                id=1,
                submission_id=1,
                verdict=enum.VerdictType.accepted,
                total_time=100,
                max_memory=100,
                score=10,
                error_message=None,
                judge_time=datetime(2023, 7, 29, 12),
            )},
            self.problems[1].id: {2: do.Judgment(
                id=1,
                submission_id=1,
                verdict=enum.VerdictType.accepted,
                total_time=100,
                max_memory=100,
                score=10,
                error_message=None,
                judge_time=datetime(2023, 7, 29, 12),
            )}
        }
        self.essay_to_member_essay_submissions = {
            self.essays[0].id: {1: do.EssaySubmission(
                id=1,
                account_id=1,
                essay_id=1,
                content_file_uuid=UUID('{12345678-1234-5678-1234-567812345678}'),
                filename='test1',
                submit_time=datetime(2023, 7, 29, 12),
            )},
            self.essays[1].id: {2: do.EssaySubmission(
                id=1,
                account_id=1,
                essay_id=1,
                content_file_uuid=UUID('{12345678-1234-5678-1234-567812345678}'),
                filename='test1',
                submit_time=datetime(2023, 7, 29, 12),
            )},
        }

        self.expected_happy_flow_result = [
            (1, [(1, self.problem_to_member_judgments[1][1])], [self.essay_to_member_essay_submissions[1][1]]),
            (2, [(2, self.problem_to_member_judgments[2][2])], [self.essay_to_member_essay_submissions[2][2]]),
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_class_ = controller.mock_module('persistence.database.class_')
            db_problem = controller.mock_module('persistence.database.problem')
            db_essay = controller.mock_module('persistence.database.essay')
            db_judgment = controller.mock_module('persistence.database.judgment')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')

            db_challenge.async_func('read').call_with(
                self.challenge_id,
            ).returns(self.challenge)
            db_class_.async_func('browse_members').call_with(
                class_id=self.challenge.class_id,
            ).returns(self.class_members)
            db_problem.async_func('browse_by_challenge').call_with(
                challenge_id=self.challenge_id,
            ).returns(self.problems)
            db_essay.async_func('browse_by_challenge').call_with(
                challenge_id=self.challenge_id,
            ).returns(self.essays)

            db_judgment.async_func('browse_by_problem_class_members').call_with(
                problem_id=self.problems[0].id, selection_type=self.challenge.selection_type,
            ).returns(self.problem_to_member_judgments[self.problems[0].id])
            db_judgment.async_func('browse_by_problem_class_members').call_with(
                problem_id=self.problems[1].id, selection_type=self.challenge.selection_type,
            ).returns(self.problem_to_member_judgments[self.problems[1].id])

            db_essay_submission.async_func('browse_by_essay_class_members').call_with(
                essay_id=self.essays[0].id,
            ).returns(self.essay_to_member_essay_submissions[self.essays[0].id])
            db_essay_submission.async_func('browse_by_essay_class_members').call_with(
                essay_id=self.essays[1].id,
            ).returns(self.essay_to_member_essay_submissions[self.essays[1].id])

            result = await statistics.get_member_submission_statistics(self.challenge_id)

        self.assertCountEqual(result, self.expected_happy_flow_result)


class TestGetProblemStatistics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.problem_id = 1
        self.expected_happy_flow_result = (1, 1, 1)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_problem = controller.mock_module('persistence.database.problem')
            db_problem.async_func('total_ac_member_count').call_with(
                self.problem_id,
            ).returns(1)
            db_problem.async_func('total_submission_count').call_with(
                self.problem_id,
            ).returns(1)
            db_problem.async_func('total_member_count').call_with(
                self.problem_id,
            ).returns(1)

            result = await statistics.get_problem_statistics(self.problem_id)

        self.assertEqual(result, self.expected_happy_flow_result)
