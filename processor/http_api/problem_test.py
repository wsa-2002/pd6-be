import copy
from datetime import datetime
import io
import typing
import unittest
from uuid import UUID

from fastapi import UploadFile, BackgroundTasks

import const
import exceptions as exc
from base import enum, do
from util import mock, model, security

from . import problem


class TestBrowseProblemSet(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.request_time = datetime(2023, 7, 29, 14, 36, 0)
        self.expected_output = [
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

    async def test_happy_flow(self) -> None:
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')

            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)
            db_problem.async_func('browse_problem_set').call_with(
                request_time=self.request_time
            ).returns(self.expected_output)

            result = await mock.unwrap(problem.browse_problem_set)()

        self.assertEqual(result, self.expected_output)

    async def test_no_permission(self) -> None:
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            service_rbac = controller.mock_module('service.rbac')
            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.browse_problem_set)()


class TestReadProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem = do.Problem(
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
        )
        self.request_time = datetime(2023, 7, 29, 12)
        self.public_challenge = do.Challenge(
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
        self.hidden_challenge = copy.deepcopy(self.public_challenge)
        self.hidden_challenge.publicize_type = enum.ChallengePublicizeType.end_time

        self.problem_with_customized_setting = copy.deepcopy(self.problem)
        self.problem_with_customized_setting.judge_type = enum.ProblemJudgeType.customized
        self.problem_with_customized_setting.setting_id = 1

        self.problem_with_reviser_setting = copy.deepcopy(self.problem)
        self.problem_with_reviser_setting.reviser_settings = [
            do.ProblemReviserSetting(id=1, type=enum.ReviserSettingType.customized),
        ]

        self.customized_setting = do.ProblemJudgeSettingCustomized(
            id=1,
            judge_code_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            judge_code_filename='filename',
        )
        self.reviser_setting = do.ProblemReviserSettingCustomized(
            id=1,
            judge_code_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            judge_code_filename='filename',
        )

        self.expected_output_happy_flow = problem.ReadProblemOutput(
            id=self.problem.id,
            challenge_id=self.problem.challenge_id,
            challenge_label=self.problem.challenge_label,
            title=self.problem.title,
            judge_type=self.problem.judge_type,
            setter_id=self.problem.setter_id,
            full_score=self.problem.full_score,
            description=self.problem.description,
            io_description=self.problem.io_description,
            source=self.problem.source,
            hint=self.problem.hint,
            is_deleted=self.problem.is_deleted,
            judge_source=None,
            reviser_is_enabled=False,
            reviser=None,
        )

        self.expected_output_with_customized_setting = copy.deepcopy(self.expected_output_happy_flow)
        self.expected_output_with_customized_setting.judge_type = enum.ProblemJudgeType.customized
        self.expected_output_with_customized_setting.judge_source = problem.JudgeSource(
            judge_language=const.TEMPORARY_CUSTOMIZED_JUDGE_LANGUAGE,
            code_uuid=self.customized_setting.judge_code_file_uuid,
            filename=self.customized_setting.judge_code_filename,
        )

        self.expected_output_with_reviser_setting = copy.deepcopy(self.expected_output_happy_flow)
        self.expected_output_with_reviser_setting.reviser_is_enabled = True
        self.expected_output_with_reviser_setting.reviser = problem.ProblemReviser(
            judge_language=const.TEMPORARY_CUSTOMIZED_REVISER_LANGUAGE,
            code_uuid=self.reviser_setting.judge_code_file_uuid,
            filename=self.reviser_setting.judge_code_filename,
        )

    async def test_happy_flow_manager_hidden(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)
            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                self.account.id, problem_id=1,
            ).returns(enum.RoleType.manager)
            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)

            db_problem.async_func('read').call_with(
                self.problem.id,
            ).returns(self.problem)
            db_challenge.async_func('read').call_with(
                self.problem.challenge_id,
            ).returns(self.public_challenge)

            result = await mock.unwrap(problem.read_problem)(self.problem.id)

        self.assertEqual(result, self.expected_output_happy_flow)

    async def test_happy_flow_normal_public(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)
            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                self.account.id, problem_id=1,
            ).returns(enum.RoleType.normal)
            service_rbac.async_func('validate_system').call_with(
                self.account.id, enum.RoleType.normal,
            ).returns(True)

            db_problem.async_func('read').call_with(
                self.problem.id,
            ).returns(self.problem)
            db_challenge.async_func('read').call_with(
                self.problem.challenge_id,
            ).returns(self.public_challenge)

            result = await mock.unwrap(problem.read_problem)(self.problem.id)

        self.assertEqual(result, self.expected_output_happy_flow)

    async def test_system_normal_hidden(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)
            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, problem_id=self.problem.id,
            ).returns(None)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            db_problem.async_func('read').call_with(
                self.problem.id,
            ).returns(self.problem)
            db_challenge.async_func('read').call_with(
                self.hidden_challenge.id,
            ).returns(self.hidden_challenge)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.read_problem)(self.hidden_challenge.id)

    async def test_manager_read_customize_judge(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_customized_judge = controller.mock_module('persistence.database.problem_judge_setting_customized')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, problem_id=self.problem.id,
            ).returns(enum.RoleType.manager)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal
            ).returns(True)
            db_problem.async_func('read').call_with(
                self.problem.id,
            ).returns(self.problem_with_customized_setting)
            db_challenge.async_func('read').call_with(
                self.problem.challenge_id,
            ).returns(self.public_challenge)
            db_customized_judge.async_func('read').call_with(
                customized_id=self.problem_with_customized_setting.setting_id,
            ).returns(self.customized_setting)
            result = await mock.unwrap(problem.read_problem)(problem_id=self.problem.id)

        self.assertEqual(result, self.expected_output_with_customized_setting)

    async def test_manager_read_revisers(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            context.set_request_time(self.request_time)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_reviser_setting = controller.mock_module('persistence.database.problem_reviser_settings')

            service_rbac.async_func('get_class_role').call_with(
                context.account.id, problem_id=self.problem.id,
            ).returns(enum.RoleType.manager)
            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)

            db_problem.async_func('read').call_with(
                self.problem_with_reviser_setting.id,
            ).returns(self.problem_with_reviser_setting)
            db_challenge.async_func('read').call_with(
                self.public_challenge.id,
            ).returns(self.public_challenge)

            db_reviser_setting.async_func('read_customized').call_with(
                customized_id=self.problem_with_reviser_setting.reviser_settings[0].id,
            ).returns(self.reviser_setting)

            result = await mock.unwrap(problem.read_problem)(self.problem.id)

        self.assertEqual(result, self.expected_output_with_reviser_setting)


class TestEditProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.problem_id = 1
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.judge_code = 'code'
        self.judge_code_byte = io.BytesIO(self.judge_code.encode(const.JUDGE_CODE_ENCODING))
        self.data = problem.EditProblemInput(
            challenge_label='label',
            title='title',
            full_score=0,
            testcase_disabled=True,
            description='desc',
            io_description='io_desc',
            source='src',
            hint='hint',
            judge_type=enum.ProblemJudgeType.customized,
            judge_source=problem.JudgeSourceInput(
                judge_language=const.TEMPORARY_CUSTOMIZED_JUDGE_LANGUAGE,
                judge_code=self.judge_code,
            ),
            reviser_is_enabled=True,
            reviser=problem.CustomizedReviserInput(
                judge_language=const.TEMPORARY_CUSTOMIZED_REVISER_LANGUAGE,
                judge_code=self.judge_code,
            ),
            is_lazy_judge=True,
        )
        self.disable_reviser_data = problem.EditProblemInput(
            judge_type=enum.ProblemJudgeType.normal,
            reviser_is_enabled=False,
        )
        self.no_update_data = problem.EditProblemInput(
            judge_type=enum.ProblemJudgeType.normal,
        )
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.setting_id = 1
        self.reviser_setting_id = 1
        self.reviser_settings = [
            do.ProblemReviserSetting(
                id=self.reviser_setting_id,
                type=enum.ReviserSettingType.customized,
            )
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            s3_customized_code = controller.mock_module('persistence.s3.customized_code')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_customized_judge = controller.mock_module('persistence.database.problem_judge_setting_customized')  # noqa
            db_reviser_setting = controller.mock_module('persistence.database.problem_reviser_settings')
            db_problem = controller.mock_module('persistence.database.problem')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            s3_customized_code.async_func('upload').call_with(
                file=mock.AnyInstanceOf(io.BytesIO),
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(
                s3_file=self.s3_file,
            ).returns(self.s3_file.uuid)
            db_customized_judge.async_func('add').call_with(
                judge_code_file_uuid=self.s3_file.uuid,
                judge_code_filename=str(self.s3_file.uuid),
            ).returns(self.setting_id)

            s3_customized_code.async_func('upload').call_with(
                file=mock.AnyInstanceOf(io.BytesIO),
            ).returns(self.s3_file)

            db_s3_file.async_func('add_with_do').call_with(
                s3_file=self.s3_file,
            ).returns(self.s3_file.uuid)

            db_reviser_setting.async_func('add_customized').call_with(
                judge_code_file_uuid=self.s3_file.uuid,
                judge_code_filename=str(self.s3_file.uuid),
            ).returns(self.reviser_setting_id)

            db_problem.async_func('edit').call_with(
                self.problem_id, challenge_label=self.data.challenge_label, title=self.data.title,
                full_score=self.data.full_score,
                description=self.data.description, io_description=self.data.io_description, source=self.data.source,
                hint=self.data.hint, setting_id=self.setting_id, judge_type=self.data.judge_type,
                reviser_settings=self.reviser_settings, is_lazy_judge=self.data.is_lazy_judge,
            ).returns(None)

            db_testcase.async_func('disable_enable_testcase_by_problem').call_with(
                problem_id=self.problem_id,
                testcase_disabled=self.data.testcase_disabled,
            ).returns(None)

            result = await mock.unwrap(problem.edit_problem)(problem_id=self.problem_id, data=self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)
            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.edit_problem)(problem_id=self.problem_id, data=self.data)

    async def test_illegal_input_wrong_customized_judge_language(self):
        data = copy.deepcopy(self.data)
        data.judge_source.judge_language = 'go'

        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)
            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(problem.edit_problem)(problem_id=self.problem_id, data=data)

    async def test_illegal_input_wrong_reviser_language(self):
        data = copy.deepcopy(self.data)
        data.reviser.judge_language = 'go'
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            s3_customized_code = controller.mock_module('persistence.s3.customized_code')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_customized_judge = controller.mock_module('persistence.database.problem_judge_setting_customized')  # noqa

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            s3_customized_code.async_func('upload').call_with(
                file=mock.AnyInstanceOf(io.BytesIO),
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(
                s3_file=self.s3_file,
            ).returns(self.s3_file.uuid)
            db_customized_judge.async_func('add').call_with(
                judge_code_file_uuid=self.s3_file.uuid,
                judge_code_filename=str(self.s3_file.uuid),
            ).returns(self.setting_id)

            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(problem.edit_problem)(problem_id=self.problem_id, data=data)

    async def test_illegal_input_customized_with_no_judge_source(self):
        data = copy.deepcopy(self.data)
        data.judge_source = None

        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)
            with self.assertRaises(exc.IllegalInput):
                await mock.unwrap(problem.edit_problem)(problem_id=self.problem_id, data=data)

    async def test_disable_reviser(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            db_problem.async_func('edit').call_with(
                self.problem_id, challenge_label=self.disable_reviser_data.challenge_label,
                title=self.disable_reviser_data.title,
                full_score=self.disable_reviser_data.full_score,
                description=self.disable_reviser_data.description,
                io_description=self.disable_reviser_data.io_description, source=self.disable_reviser_data.source,
                hint=self.disable_reviser_data.hint, setting_id=None, judge_type=self.disable_reviser_data.judge_type,
                reviser_settings=[], is_lazy_judge=self.disable_reviser_data.is_lazy_judge,
            ).returns(None)

            result = await mock.unwrap(problem.edit_problem)(problem_id=self.problem_id, data=self.disable_reviser_data)

        self.assertIsNone(result)

    async def test_no_update(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            db_problem.async_func('edit').call_with(
                self.problem_id, challenge_label=self.no_update_data.challenge_label,
                title=self.no_update_data.title,
                full_score=self.no_update_data.full_score,
                description=self.no_update_data.description,
                io_description=self.no_update_data.io_description, source=self.no_update_data.source,
                hint=self.no_update_data.hint, setting_id=None, judge_type=self.no_update_data.judge_type,
                reviser_settings=..., is_lazy_judge=self.no_update_data.is_lazy_judge,
            ).returns(None)

            result = await mock.unwrap(problem.edit_problem)(problem_id=self.problem_id, data=self.no_update_data)

        self.assertIsNone(result)


class TestDeleteProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            service_rbac = controller.mock_module('service.rbac')
            db_problem = controller.mock_module('persistence.database.problem')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)
            db_problem.async_func('delete').call_with(
                problem_id=self.problem_id,
            ).returns(None)

            result = await mock.unwrap(problem.delete_problem)(problem_id=self.problem_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)
            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.delete_problem)(problem_id=self.problem_id)


class TestAddTestCaseUnderProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.testcase_id = 1
        self.data = problem.AddTestcaseInput(
            is_sample=True,
            score=1,
            time_limit=1000,
            memory_limit=1000,
            note='note',
            is_disabled=False,
            label='label',
        )
        self.expected_output = model.AddOutput(id=self.testcase_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)
            db_testcase.async_func('add').call_with(
                problem_id=self.problem_id, is_sample=self.data.is_sample, score=self.data.score,
                label=self.data.label, input_file_uuid=None, output_file_uuid=None,
                input_filename=None, output_filename=None,
                time_limit=self.data.time_limit, memory_limit=self.data.memory_limit,
                is_disabled=self.data.is_disabled, note=self.data.note,
            ).returns(self.testcase_id)

            result = await mock.unwrap(problem.add_testcase_under_problem)(problem_id=self.problem_id, data=self.data)

        self.assertEqual(result, self.expected_output)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.add_testcase_under_problem)(problem_id=self.problem_id, data=self.data)  # noqa


class BrowseAllTestcaseUnderProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.testcases = [
            do.Testcase(
                id=1,
                problem_id=self.problem_id,
                is_sample=False,
                score=100,
                label='label',
                input_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                output_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                input_filename='None',
                output_filename='None',
                note='note',
                time_limit=1000,
                memory_limit=1000,
                is_disabled=False,
                is_deleted=True,
            ),
            do.Testcase(
                id=2,
                problem_id=self.problem_id,
                is_sample=True,
                score=100,
                label='label',
                input_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                output_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                input_filename='None',
                output_filename='None',
                note='note',
                time_limit=1000,
                memory_limit=1000,
                is_disabled=True,
                is_deleted=True,
            ),
        ]
        self.expected_output = [
            problem.ReadTestcaseOutput(**testcase.__dict__) for testcase in self.testcases
        ]
        self.expected_output_without_file_uuid = copy.deepcopy(self.expected_output)
        for testcase in self.expected_output_without_file_uuid:
            if not testcase.is_sample:
                testcase.input_file_uuid = None
                testcase.output_file_uuid = None

    async def test_happy_flow_cm(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            db_testcase.async_func('browse').call_with(
                problem_id=self.problem_id, include_disabled=True,
            ).returns(self.testcases)

            result = await mock.unwrap(problem.browse_all_testcase_under_problem)(problem_id=self.problem_id)

        self.assertEqual(result, self.expected_output)

    async def test_happy_flow_sn(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_testcase = controller.mock_module('persistence.database.testcase')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            db_testcase.async_func('browse').call_with(
                problem_id=self.problem_id, include_disabled=True,
            ).returns(self.testcases)

            result = await mock.unwrap(problem.browse_all_testcase_under_problem)(problem_id=self.problem_id)

        self.assertEqual(result, self.expected_output_without_file_uuid)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.browse_all_testcase_under_problem)(problem_id=self.problem_id)


class TestBrowseAllAssistingDataUnderProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.assisting_data = [
            do.AssistingData(
                id=1,
                problem_id=1,
                s3_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                filename='filename',
                is_deleted=False,
            ),
            do.AssistingData(
                id=2,
                problem_id=1,
                s3_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                filename='filename2',
                is_deleted=False,
            ),
        ]
        self.expected_output = [
            problem.ReadAssistingDataOutput(
                id=data.id,
                problem_id=data.problem_id,
                s3_file_uuid=data.s3_file_uuid,
                filename=data.filename,
            ) for data in self.assisting_data
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            db_assisting_data = controller.mock_module('persistence.database.assisting_data')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            db_assisting_data.async_func('browse').call_with(
                problem_id=self.problem_id,
            ).returns(self.assisting_data)

            result = await mock.unwrap(problem.browse_all_assisting_data_under_problem)(problem_id=self.problem_id)

        self.assertEqual(result, self.expected_output)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.browse_all_assisting_data_under_problem)(problem_id=self.problem_id)


class TestAddAssistingDataUnderProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        # self.assisting_data: UploadFile = File(...)
        self.assisting_data = UploadFile(filename='filename')
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.assisting_data_id = 1
        self.expected_output = model.AddOutput(id=self.assisting_data_id)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            s3_assisting_data = controller.mock_module('persistence.s3.assisting_data')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_assisting_data = controller.mock_module('persistence.database.assisting_data')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            s3_assisting_data.async_func('upload').call_with(
                file=mock.AnyInstanceOf(type(self.assisting_data.file)),
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(
                s3_file=mock.AnyInstanceOf(type(self.s3_file)),
            ).returns(self.s3_file.uuid)

            db_assisting_data.async_func('add').call_with(
                problem_id=self.problem_id, s3_file_uuid=self.s3_file.uuid,
                filename=self.assisting_data.filename,
            ).returns(self.assisting_data_id)

            result = await mock.unwrap(problem.add_assisting_data_under_problem)(problem_id=self.problem_id, assisting_data=self.assisting_data)  # noqa

        self.assertEqual(result, self.expected_output)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                result = await mock.unwrap(problem.add_assisting_data_under_problem)(problem_id=self.problem_id, assisting_data=self.assisting_data)  # noqa


class TestDownloadAllAssistingData(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.background_tasks = BackgroundTasks()
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'assisting_data.zip'
        self.file_url = 'file_url'
        self.account = do.Account(
            id=1,
            username='username',
            nickname='',
            real_name='',
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email=None,
        )
        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='1',
            email='email',
            is_default=True,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(problem.download_all_assisting_data)(problem_id=self.problem_id,
                                                                            as_attachment=True,
                                                                            background_tasks=self.background_tasks)
            service_downloader.async_func('all_assisting_data').call_with(
                problem_id=self.problem_id,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                filename=self.filename, as_attachment=True,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(self.account, self.student_card)

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email, file_url=self.file_url,
            ).returns(None)

            await todo_async_task()

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.download_all_assisting_data)(problem_id=self.problem_id,
                                                                       as_attachment=True,
                                                                       background_tasks=self.background_tasks)


class TestDownloadAllSampleTestcase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.background_tasks = BackgroundTasks()
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'sample_testcase.zip'
        self.file_url = 'file_url'
        self.account = do.Account(
            id=1,
            username='username',
            nickname='',
            real_name='',
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email=None,
        )
        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='1',
            email='email',
            is_default=True,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(problem.download_all_sample_testcase)(problem_id=self.problem_id,
                                                                             as_attachment=True,
                                                                             background_tasks=self.background_tasks)

            service_downloader.async_func('all_testcase').call_with(
                problem_id=self.problem_id, is_sample=True,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                filename=self.filename, as_attachment=True,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(self.account, self.student_card)

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email, file_url=self.file_url,
            ).returns(None)
            await todo_async_task()

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.download_all_sample_testcase)(problem_id=self.problem_id,
                                                                        as_attachment=True,
                                                                        background_tasks=self.background_tasks)


class TestDownloadAllNonSampleTestcase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.background_tasks = BackgroundTasks()
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket='temp',
            key='d8ec7a6a-27e1-4cee-8229-4304ef933544',
        )
        self.filename = 'non_sample_testcase.zip'
        self.file_url = 'file_url'
        self.account = do.Account(
            id=1,
            username='username',
            nickname='',
            real_name='',
            role=enum.RoleType.normal,
            is_deleted=False,
            alternative_email=None,
        )
        self.student_card = do.StudentCard(
            id=1,
            institute_id=1,
            student_id='1',
            email='email',
            is_default=True,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            util_background_task = controller.mock_module('util.background_task')
            service_downloader = controller.mock_module('service.downloader')
            s3_tools = controller.mock_module('persistence.s3.tools')
            db_account_vo = controller.mock_module('persistence.database.account_vo')
            email_notification = controller.mock_module('persistence.email.notification')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            todo_async_task: typing.Callable[..., typing.Awaitable] = None  # noqa

            def _set_task(_, async_task):
                nonlocal todo_async_task
                todo_async_task = async_task

            util_background_task.func('launch').call_with(
                mock.AnyInstanceOf(type(self.background_tasks)), mock.AnyInstanceOf(object),
            ).executes(_set_task)

            result = await mock.unwrap(problem.download_all_non_sample_testcase)(problem_id=self.problem_id,
                                                                                 as_attachment=True,
                                                                                 background_tasks=self.background_tasks)

            service_downloader.async_func('all_testcase').call_with(
                problem_id=self.problem_id, is_sample=False,
            ).returns(self.s3_file)
            s3_tools.async_func('sign_url').call_with(
                bucket=self.s3_file.bucket, key=self.s3_file.key,
                filename=self.filename, as_attachment=True,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
            ).returns(self.file_url)

            db_account_vo.async_func('read_with_default_student_card').call_with(
                account_id=context.account.id,
            ).returns(self.account, self.student_card)

            email_notification.async_func('send_file_download_url').call_with(
                to=self.student_card.email, file_url=self.file_url,
            ).returns(None)
            await todo_async_task()

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.download_all_non_sample_testcase)(problem_id=self.problem_id,
                                                                            as_attachment=True,
                                                                            background_tasks=self.background_tasks)


class TestGetScoreByChallengeTypeUnderProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem = do.Problem(
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
        )
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
        self.submission_judgment = do.Judgment(
            id=1,
            submission_id=1,
            verdict=enum.VerdictType.accepted,
            total_time=1000,
            max_memory=1000,
            score=100,
            error_message='',
            judge_time=datetime(2023, 7, 29, 12),
        )
        self.expected_output = problem.GetScoreByTypeOutput(
            challenge_type=self.challenge.selection_type,
            score=self.submission_judgment.score,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            db_problem = controller.mock_module('persistence.database.problem')
            db_challenge = controller.mock_module('persistence.database.challenge')
            db_judgment = controller.mock_module('persistence.database.judgment')

            db_problem.async_func('read').call_with(
                self.problem.id,
            ).returns(self.problem)
            db_challenge.async_func('read').call_with(
                challenge_id=self.problem.challenge_id,
            ).returns(self.challenge)
            db_judgment.async_func('read_by_challenge_type').call_with(
                problem_id=self.problem.id,
                account_id=context.account.id,
                selection_type=self.challenge.selection_type,
                challenge_end_time=self.challenge.end_time,
            ).returns(self.submission_judgment)

            result = await mock.unwrap(problem.get_score_by_challenge_type_under_problem)(problem_id=self.problem.id)

        self.assertEqual(result, self.expected_output)


class TestGetScoreByBestUnderProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem = do.Problem(
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
        )
        self.submission_judgment = do.Judgment(
            id=1,
            submission_id=1,
            verdict=enum.VerdictType.accepted,
            total_time=1000,
            max_memory=1000,
            score=100,
            error_message='',
            judge_time=datetime(2023, 7, 29, 12),
        )
        self.expected_output = problem.GetScoreByTypeOutput(
            challenge_type=enum.TaskSelectionType.best,
            score=self.submission_judgment.score,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            db_problem = controller.mock_module('persistence.database.problem')
            db_judgment = controller.mock_module('persistence.database.judgment')

            db_problem.async_func('read').call_with(
                self.problem.id,
            ).returns(self.problem)
            db_judgment.async_func('get_best_submission_judgment_all_time').call_with(
                problem_id=self.problem.id,
                account_id=context.account.id,
            ).returns(self.submission_judgment)

            result = await mock.unwrap(problem.get_score_by_best_under_problem)(problem_id=self.problem.id)

        self.assertEqual(result, self.expected_output)


class TestRejudgeProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.rejudged_submissions = [
            do.Submission(
                id=1,
                account_id=1,
                problem_id=1,
                language_id=1,
                content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                content_length=1,
                filename='filename',
                submit_time=datetime(2023, 7, 29),
            ),
            do.Submission(
                id=2,
                account_id=1,
                problem_id=1,
                language_id=1,
                content_file_uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
                content_length=1,
                filename='filename',
                submit_time=datetime(2023, 7, 29),
            ),
        ]
        self.expected_output = problem.RejudgeProblemOutput(submission_count=len(self.rejudged_submissions))

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_judge = controller.mock_module('service.judge')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(True)

            service_judge.async_func('judge_problem_submissions').call_with(
                self.problem_id,
            ).returns(self.rejudged_submissions)

            result = await mock.unwrap(problem.rejudge_problem)(problem_id=self.problem_id)

        self.assertEqual(result, self.expected_output)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, problem_id=self.problem_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.rejudge_problem)(problem_id=self.problem_id)


class TestGetProblemStatistics(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account = security.AuthedAccount(id=1, cached_username='username')
        self.problem_id = 1
        self.statistics = (1, 2, 3)
        self.expected_output = problem.GetProblemStatOutput(
            solved_member_count=1,
            submission_count=2,
            member_count=3,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')
            service_statistics = controller.mock_module('service.statistics')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)

            service_statistics.async_func('get_problem_statistics').call_with(
                problem_id=self.problem_id,
            ).returns(self.statistics)

            result = await mock.unwrap(problem.get_problem_statistics)(problem_id=self.problem_id)

        self.assertEqual(result, self.expected_output)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(problem.get_problem_statistics)(problem_id=self.problem_id)
