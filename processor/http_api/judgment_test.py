import copy
import datetime
import unittest
import uuid

from base import enum, do
import exceptions as exc
from util import mock, security

from . import judgment


class TestBrowseAllJudgmentVerdict(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.result = ['ACCEPTED', 'WRONG ANSWER', 'MEMORY LIMIT EXCEED', 'TIME LIMIT EXCEED', 'RUNTIME ERROR',
                       'COMPILE ERROR', 'CONTACT MANAGER', 'FORBIDDEN ACTION', 'SYSTEM ERROR']

    async def test_happy_flow(self):
        result = await mock.unwrap(judgment.browse_all_judgment_verdict)()

        self.assertCountEqual(result, self.result)


class TestReadJudgment(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='manager')
        self.today = datetime.datetime(2023, 4, 9)
        self.judgment_id = 1
        self.judgment = do.Judgment(
            id=1,
            submission_id=1,
            verdict=enum.VerdictType.accepted,
            total_time=100,
            max_memory=100,
            score=10,
            error_message=None,
            judge_time=self.today,
        )
        self.submission = do.Submission(
            id=self.judgment.submission_id,
            account_id=self.login_account.id,
            problem_id=1,
            language_id=1,
            content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            content_length=100,
            filename='test',
            submit_time=self.today,
        )
        self.result = copy.deepcopy(self.judgment)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_judgment = controller.mock_module('persistence.database.judgment')
            db_submission = controller.mock_module('persistence.database.submission')

            db_judgment.async_func('read').call_with(
                judgment_id=self.judgment_id,
            ).returns(self.judgment)
            db_submission.async_func('read').call_with(
                submission_id=self.judgment.submission_id,
            ).returns(self.submission)

            result = await mock.unwrap(judgment.read_judgment)(self.judgment_id)

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_judgment = controller.mock_module('persistence.database.judgment')
            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_judgment.async_func('read').call_with(
                judgment_id=self.judgment_id,
            ).returns(self.judgment)
            db_submission.async_func('read').call_with(
                submission_id=self.judgment.submission_id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, submission_id=self.submission.id,
            ).returns(True)

            result = await mock.unwrap(judgment.read_judgment)(self.judgment_id)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_judgment = controller.mock_module('persistence.database.judgment')
            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_judgment.async_func('read').call_with(
                judgment_id=self.judgment_id,
            ).returns(self.judgment)
            db_submission.async_func('read').call_with(
                submission_id=self.judgment.submission_id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, submission_id=self.submission.id,
            ).returns(False)
            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(judgment.read_judgment)(self.judgment_id)


class TestBrowseAllJudgmentJudgeCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.other_account = security.AuthedAccount(id=2, cached_username='manager')
        self.today = datetime.datetime(2023, 4, 9)
        self.judgment_id = 1
        self.judgment = do.Judgment(
            id=1,
            submission_id=1,
            verdict=enum.VerdictType.accepted,
            total_time=100,
            max_memory=100,
            score=10,
            error_message=None,
            judge_time=self.today,
        )
        self.submission = do.Submission(
            id=self.judgment.submission_id,
            account_id=self.login_account.id,
            problem_id=1,
            language_id=1,
            content_file_uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            content_length=100,
            filename='test',
            submit_time=self.today,
        )
        self.judge_case = [
            do.JudgeCase(
                judgment_id=self.judgment_id,
                testcase_id=1,
                verdict=enum.VerdictType.compile_error,
                time_lapse=5,
                peak_memory=5,
                score=0,
            ),
            do.JudgeCase(
                judgment_id=self.judgment_id,
                testcase_id=2,
                verdict=enum.VerdictType.accepted,
                time_lapse=70,
                peak_memory=70,
                score=10,
            ),
        ]
        self.result = copy.deepcopy(self.judge_case)

    async def test_happy_flow_self(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            db_judgment = controller.mock_module('persistence.database.judgment')
            db_submission = controller.mock_module('persistence.database.submission')

            db_judgment.async_func('read').call_with(
                judgment_id=self.judgment_id,
            ).returns(self.judgment)
            db_submission.async_func('read').call_with(
                submission_id=self.judgment.submission_id,
            ).returns(self.submission)
            db_judgment.async_func('browse_cases').call_with(judgment_id=self.judgment_id).returns(self.judge_case)

            result = await mock.unwrap(judgment.browse_all_judgment_judge_case)(self.judgment_id)

        self.assertEqual(result, self.result)

    async def test_happy_flow_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_judgment = controller.mock_module('persistence.database.judgment')
            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_judgment.async_func('read').call_with(
                judgment_id=self.judgment_id,
            ).returns(self.judgment)
            db_submission.async_func('read').call_with(
                submission_id=self.judgment.submission_id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, submission_id=self.submission.id,
            ).returns(True)
            db_judgment.async_func('browse_cases').call_with(judgment_id=self.judgment_id).returns(self.judge_case)

            result = await mock.unwrap(judgment.browse_all_judgment_judge_case)(self.judgment_id)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.other_account)

            db_judgment = controller.mock_module('persistence.database.judgment')
            db_submission = controller.mock_module('persistence.database.submission')
            service_rbac = controller.mock_module('service.rbac')

            db_judgment.async_func('read').call_with(
                judgment_id=self.judgment_id,
            ).returns(self.judgment)
            db_submission.async_func('read').call_with(
                submission_id=self.judgment.submission_id,
            ).returns(self.submission)
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, submission_id=self.submission.id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(judgment.browse_all_judgment_judge_case)(self.judgment_id)
