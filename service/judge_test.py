import copy
import datetime
import unittest
import uuid

import common.do
import common.const
from base import enum, do, popo
import const
from util import mock

from . import judge


class TestJudgeSubmission(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.submission_id = 1
        self.submission = do.Submission(
            id=1,
            account_id=1,
            problem_id=1,
            language_id=1,
            content_file_uuid=uuid.UUID('12345678123456781234567812345678'),
            content_length=10,
            filename='submission',
            submit_time=datetime.datetime(2023, 4, 9),
        )
        self.judge_problem = common.do.Problem(
            full_score=20,
            is_lazy_judge=False,
        )
        self.judge_testcases = [
            common.do.Testcase(
                id=1,
                score=0,
                label='sample',
                is_sample=True,
                input_file_url=None,
                output_file_url=None,
                time_limit=1000,
                memory_limit=1024,
            ),
            common.do.Testcase(
                id=2,
                score=20,
                label='non_testcase',
                is_sample=False,
                input_file_url=None,
                output_file_url=None,
                time_limit=1000,
                memory_limit=1024,
            ),
        ]
        self.judge_assisting_datas = [
            common.do.AssistingData(
                file_url='.../assisting_data',
                filename='assisting_data',
            ),
        ]
        self.customized_judge_setting = common.do.CustomizedJudgeSetting(
            file_url='.../customized_judge_setting',
        )
        self.reviser_settings = [
            common.do.ReviserSetting(
                file_url='.../reviser_settings',
            ),
        ]

    async def test_happy_flow(self):
        with mock.Controller() as controller:
            db_submission = controller.mock_module('persistence.database.submission')

            db_submission.async_func('read').call_with(self.submission_id).returns(self.submission)
            controller.mock_global_async_func('service.judge._prepare_problem').call_with(
                self.submission.problem_id,
            ).returns(
                self.judge_problem, self.judge_testcases, self.judge_assisting_datas,
                self.customized_judge_setting, self.reviser_settings,
            )
            controller.mock_global_async_func('service.judge._judge').call_with(
                self.submission, judge_problem=self.judge_problem, priority=common.const.PRIORITY_SUBMIT,
                judge_testcases=self.judge_testcases, judge_assisting_datas=self.judge_assisting_datas,
                customized_judge_setting=self.customized_judge_setting, reviser_settings=self.reviser_settings,
            ).returns(None)

            result = await judge.judge_submission(self.submission_id, False)

        self.assertIsNone(result)

    async def test_happy_flow_rejudge(self):
        with mock.Controller() as controller:
            db_submission = controller.mock_module('persistence.database.submission')

            db_submission.async_func('read').call_with(self.submission_id).returns(self.submission)
            controller.mock_global_async_func('service.judge._prepare_problem').call_with(
                self.submission.problem_id,
            ).returns(
                self.judge_problem, self.judge_testcases, self.judge_assisting_datas,
                self.customized_judge_setting, self.reviser_settings,
            )
            controller.mock_global_async_func('service.judge._judge').call_with(
                self.submission, judge_problem=self.judge_problem, priority=common.const.PRIORITY_REJUDGE_SINGLE,
                judge_testcases=self.judge_testcases, judge_assisting_datas=self.judge_assisting_datas,
                customized_judge_setting=self.customized_judge_setting, reviser_settings=self.reviser_settings,
            ).returns(None)

            result = await judge.judge_submission(self.submission_id, True)

        self.assertIsNone(result)


class TestJudgeProblemSubmissions(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.problem_id = 1
        self.judge_problem = common.do.Problem(
            full_score=20,
            is_lazy_judge=False,
        )
        self.judge_testcases = [
            common.do.Testcase(
                id=1,
                score=0,
                label='sample',
                is_sample=True,
                input_file_url=None,
                output_file_url=None,
                time_limit=1000,
                memory_limit=1024,
            ),
            common.do.Testcase(
                id=2,
                score=20,
                label='non_testcase',
                is_sample=False,
                input_file_url=None,
                output_file_url=None,
                time_limit=1000,
                memory_limit=1024,
            ),
        ]
        self.judge_assisting_datas = [
            common.do.AssistingData(
                file_url='.../assisting_data',
                filename='assisting_data',
            ),
        ]
        self.customized_judge_setting = [
            common.do.CustomizedJudgeSetting(
                file_url='.../customized_judge_setting',
            ),
        ]
        self.reviser_settings = [
            common.do.ReviserSetting(
                file_url='.../reviser_settings',
            ),
        ]
        self.offset = 0
        self.batch_size = 100

        self.batch_submissions = [
            do.Submission(
                id=1,
                account_id=1,
                problem_id=1,
                language_id=1,
                content_file_uuid=uuid.UUID('12345678123456781234567812345678'),
                content_length=10,
                filename='submission',
                submit_time=datetime.datetime(2023, 4, 9),
            ),
            do.Submission(
                id=2,
                account_id=2,
                problem_id=1,
                language_id=1,
                content_file_uuid=uuid.UUID('12345678123456781234567812345679'),
                content_length=10,
                filename='submission',
                submit_time=datetime.datetime(2023, 4, 9),
            ),
        ]
        self.submissions = copy.deepcopy(self.batch_submissions)
        self.result = copy.deepcopy(self.submissions)

    async def test_happy_flow(self):
        with mock.Controller() as controller:
            db_submission = controller.mock_module('persistence.database.submission')

            controller.mock_global_async_func('service.judge._prepare_problem').call_with(
                self.problem_id,
            ).returns(
                self.judge_problem, self.judge_testcases, self.judge_assisting_datas,
                self.customized_judge_setting, self.reviser_settings,
            )
            db_submission.async_func('browse').call_with(
                offset=self.offset, limit=self.batch_size, filters=[
                    popo.Filter(col_name='problem_id', op=enum.FilterOperator.equal, value=self.problem_id),
                ], sorters=[]).returns((self.batch_submissions, len(self.batch_submissions)))
            db_submission.async_func('browse').call_with(
                offset=self.offset + self.batch_size, limit=self.batch_size, filters=[
                    popo.Filter(col_name='problem_id', op=enum.FilterOperator.equal, value=self.problem_id),
                ], sorters=[]).returns(([], 0))
            for submission in self.submissions:
                controller.mock_global_async_func('service.judge._judge').call_with(
                    submission, judge_problem=self.judge_problem, priority=common.const.PRIORITY_REJUDGE_BATCH,
                    judge_testcases=self.judge_testcases, judge_assisting_datas=self.judge_assisting_datas,
                    customized_judge_setting=self.customized_judge_setting, reviser_settings=self.reviser_settings,
                ).returns(None)

            result = await judge.judge_problem_submissions(self.problem_id)

        self.assertEqual(result, self.result)


class TestPrepareProblem(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.problem_id = 1
        self.problem_normal = do.Problem(
            id=self.problem_id,
            challenge_id=1,
            challenge_label='test',
            judge_type=enum.ProblemJudgeType.normal,
            setting_id=None,
            title='title',
            setter_id=1,
            full_score=20,
            description='description',
            io_description=None,
            source='.../source',
            hint='hint',
            is_lazy_judge=False,
            is_deleted=False,
            reviser_settings=[
                do.ProblemReviserSetting(
                    id=1,
                    type=enum.ReviserSettingType.customized,
                )
            ]
        )
        self.problem_customized = do.Problem(
            id=self.problem_id,
            challenge_id=1,
            challenge_label='test',
            judge_type=enum.ProblemJudgeType.customized,
            setting_id=1,
            title='title',
            setter_id=1,
            full_score=20,
            description='description',
            io_description=None,
            source='.../source',
            hint='hint',
            is_lazy_judge=False,
            is_deleted=False,
            reviser_settings=[
                do.ProblemReviserSetting(
                    id=1,
                    type=enum.ReviserSettingType.customized,
                )
            ]
        )
        self.judge_problem = common.do.Problem(
            full_score=20,
            is_lazy_judge=False,
        )
        self.testcases = [
            do.Testcase(
                id=1,
                problem_id=self.problem_id,
                is_sample=True,
                score=0,
                label='sample',
                input_file_uuid=uuid.UUID('12345678123456781234567812345678'),
                output_file_uuid=uuid.UUID('12345678123456781234567812345679'),
                input_filename='input_file',
                output_filename='output_file',
                note=None,
                time_limit=1000,
                memory_limit=1024,
                is_disabled=False,
                is_deleted=False,
            ),
            do.Testcase(
                id=2,
                problem_id=self.problem_id,
                is_sample=False,
                score=20,
                label='non_sample',
                input_file_uuid=None,
                output_file_uuid=None,
                input_filename=None,
                output_filename=None,
                note=None,
                time_limit=1000,
                memory_limit=1024,
                is_disabled=False,
                is_deleted=False,
            ),
        ]
        self.judge_testcases = [
            common.do.Testcase(
                id=1,
                score=0,
                label='sample',
                is_sample=True,
                input_file_url='.../input_file_url',
                output_file_url='.../output_file_url',
                time_limit=1000,
                memory_limit=1024,
            ),
            common.do.Testcase(
                id=2,
                score=20,
                label='non_sample',
                is_sample=False,
                input_file_url=None,
                output_file_url=None,
                time_limit=1000,
                memory_limit=1024,
            ),
        ]
        self.assisting_datas = [
            do.AssistingData(
                id=1,
                problem_id=self.problem_id,
                s3_file_uuid=uuid.UUID('12345678123456781234567812345680'),
                filename='assisting_data',
                is_deleted=False,
            ),
        ]
        self.judge_assisting_datas = [
            common.do.AssistingData(
                file_url='.../assisting_data',
                filename='assisting_data',
            ),
        ]
        self.customized_judge_setting = do.ProblemJudgeSettingCustomized(
            id=1,
            judge_code_file_uuid=uuid.UUID('12345678123456781234567812345681'),
            judge_code_filename='judge_code')
        self.judge_customized_judge_setting = common.do.CustomizedJudgeSetting(
            file_url='.../customized_judge_setting',
        )

        self.reviser_settings = [
            do.ProblemJudgeSettingCustomized(
                id=1,
                judge_code_file_uuid=uuid.UUID('12345678123456781234567812345681'),
                judge_code_filename='judge_code',
            ),
        ]
        self.judge_reviser_settings = [
            common.do.ReviserSetting(
                file_url='.../reviser_settings',
            ),
        ]
        self.result_normal = (self.judge_problem, self.judge_testcases, self.judge_assisting_datas,
                              None, self.judge_reviser_settings)
        self.result_customized = (self.judge_problem, self.judge_testcases, self.judge_assisting_datas,
                                  self.judge_customized_judge_setting, self.judge_reviser_settings)

    async def test_happy_flow_normal(self):
        with mock.Controller() as controller:
            db_problem = controller.mock_module('persistence.database.problem')
            db_testcase = controller.mock_module('persistence.database.testcase')
            db_assisting_data = controller.mock_module('persistence.database.assisting_data')
            db_problem_reviser_settings = controller.mock_module('persistence.database.problem_reviser_settings')

            db_problem.async_func('read').call_with(self.problem_id).returns(self.problem_normal)
            db_testcase.async_func('browse').call_with(self.problem_normal.id, include_disabled=False).returns(
                self.testcases)
            db_assisting_data.async_func('browse').call_with(self.problem_normal.id).returns(self.assisting_datas)
            for i, reviser_setting in enumerate(self.problem_normal.reviser_settings):
                db_problem_reviser_settings.async_func('read_customized').call_with(reviser_setting.id).returns(
                    self.reviser_settings[i],
                )
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.testcases[0].input_file_uuid, filename='0.in',
            ).returns(self.judge_testcases[0].input_file_url)
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.testcases[0].output_file_uuid, filename='0.out',
            ).returns(self.judge_testcases[0].output_file_url)
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.assisting_datas[0].s3_file_uuid, filename=self.assisting_datas[0].filename,
            ).returns(self.judge_assisting_datas[0].file_url)
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.reviser_settings[0].judge_code_file_uuid, filename=self.reviser_settings[0].judge_code_filename,
            ).returns(self.judge_reviser_settings[0].file_url)

            result = await judge._prepare_problem(self.problem_id)

        self.assertEqual(result, self.result_normal)

    async def test_happy_flow_customized(self):
        with mock.Controller() as controller:
            db_problem = controller.mock_module('persistence.database.problem')
            db_testcase = controller.mock_module('persistence.database.testcase')
            db_problem_judge_setting_customized = \
                controller.mock_module('persistence.database.problem_judge_setting_customized')
            db_assisting_data = controller.mock_module('persistence.database.assisting_data')
            db_problem_reviser_settings = controller.mock_module('persistence.database.problem_reviser_settings')

            db_problem.async_func('read').call_with(self.problem_id).returns(self.problem_customized)
            db_testcase.async_func('browse').call_with(self.problem_customized.id, include_disabled=False).returns(
                self.testcases)
            db_assisting_data.async_func('browse').call_with(self.problem_customized.id).returns(self.assisting_datas)
            db_problem_judge_setting_customized.async_func('read').call_with(
                self.problem_customized.setting_id).returns(self.customized_judge_setting)
            for i, reviser_setting in enumerate(self.problem_customized.reviser_settings):
                db_problem_reviser_settings.async_func('read_customized').call_with(reviser_setting.id).returns(
                    self.reviser_settings[i],
                )
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.testcases[0].input_file_uuid, filename='0.in',
            ).returns(self.judge_testcases[0].input_file_url)
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.testcases[0].output_file_uuid, filename='0.out',
            ).returns(self.judge_testcases[0].output_file_url)
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.assisting_datas[0].s3_file_uuid, filename=self.assisting_datas[0].filename,
            ).returns(self.judge_assisting_datas[0].file_url)
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.customized_judge_setting.judge_code_file_uuid,
                filename=self.customized_judge_setting.judge_code_filename,
            ).returns(self.judge_customized_judge_setting.file_url)
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.reviser_settings[0].judge_code_file_uuid, filename=self.reviser_settings[0].judge_code_filename,
            ).returns(self.judge_reviser_settings[0].file_url)

            result = await judge._prepare_problem(self.problem_id)

        self.assertEqual(result, self.result_customized)


class TestJudge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.submission = do.Submission(
            id=1,
            account_id=1,
            problem_id=1,
            language_id=1,
            content_file_uuid=uuid.UUID('12345678123456781234567812345678'),
            content_length=10,
            filename='submission',
            submit_time=datetime.datetime(2023, 4, 9),
        )
        self.judge_problem = common.do.Problem(
            full_score=20,
            is_lazy_judge=False,
        )
        self.priority = common.const.PRIORITY_SUBMIT
        self.judge_testcases = [
            common.do.Testcase(
                id=1,
                score=0,
                label='sample',
                is_sample=True,
                input_file_url=None,
                output_file_url=None,
                time_limit=1000,
                memory_limit=1024,
            ),
            common.do.Testcase(
                id=2,
                score=20,
                label='non_testcase',
                is_sample=False,
                input_file_url=None,
                output_file_url=None,
                time_limit=1000,
                memory_limit=1024,
            ),
        ]
        self.judge_assisting_datas = [
            common.do.AssistingData(
                file_url='.../assisting_data',
                filename='assisting_data',
            ),
        ]
        self.customized_judge_setting = common.do.CustomizedJudgeSetting(
            file_url='.../customized_judge_setting',
        )
        self.reviser_settings = [
            common.do.ReviserSetting(
                file_url='.../reviser_settings',
            ),
        ]

        self.submission_language = do.SubmissionLanguage(
            id=self.submission.language_id,
            name='cpp',
            version='17',
            is_disabled=False,
        )
        self.submission_language_disabled = do.SubmissionLanguage(
            id=self.submission.language_id,
            name='cpp',
            version='17',
            is_disabled=True,
        )
        self.file_url = '.../file_url'
        self.language_queue_name = 'cpp17'

    async def test_happy_flow(self):
        with mock.Controller() as controller:
            db_submission = controller.mock_module('persistence.database.submission')
            publisher_judge = controller.mock_module('persistence.amqp_publisher.judge')

            db_submission.async_func('read_language').call_with(self.submission.language_id).returns(
                self.submission_language,
            )
            controller.mock_global_async_func('service.judge._sign_file_url').call_with(
                self.submission.content_file_uuid, filename=self.submission.filename,
            ).returns(self.file_url)
            db_submission.async_func('read_language_queue_name').call_with(self.submission_language.id).returns(
                self.language_queue_name,
            )
            publisher_judge.async_func('send_judge').call_with(
                common.do.JudgeTask(
                    problem=self.judge_problem,
                    submission=common.do.Submission(
                        id=self.submission.id,
                        file_url=self.file_url,
                    ),
                    testcases=self.judge_testcases,
                    assisting_data=self.judge_assisting_datas,
                    customized_judge_setting=self.customized_judge_setting,
                    reviser_settings=self.reviser_settings,
                ),
                language_queue_name=self.language_queue_name,
                priority=self.priority,
            ).returns(None)

            result = await judge._judge(self.submission, self.judge_problem, self.priority,
                                        self.customized_judge_setting, self.reviser_settings,
                                        self.judge_testcases, self.judge_assisting_datas)

        self.assertIsNone(result)

    async def test_happy_flow_language_disable(self):
        with mock.Controller() as controller:
            db_submission = controller.mock_module('persistence.database.submission')

            db_submission.async_func('read_language').call_with(self.submission.language_id).returns(
                self.submission_language_disabled,
            )
            controller.mock_global_func('log.info').call_with(
                f"Submission id {self.submission.id} is skipped judge because" 
                f" submission language id {self.submission.language_id} is disabled").returns(None)

            result = await judge._judge(self.submission, self.judge_problem, self.priority,
                                        self.customized_judge_setting, self.reviser_settings,
                                        self.judge_testcases, self.judge_assisting_datas)

        self.assertIsNone(result)


# the A in name is to mess with test order, work as temporary fix
class TestASignFileUrl(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.uuid = uuid.UUID('12345678123456781234567812345678')
        self.filename = 'test'
        self.s3file = do.S3File(
            uuid=self.uuid,
            bucket='bucket',
            key='key',
        )

        self.url = '.../data'
        self.result = copy.deepcopy(self.url)

    async def test_happy_flow(self):
        with mock.Controller() as controller:
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            s3_tools = controller.mock_module('persistence.s3.tools')

            db_s3_file.async_func('read').call_with(self.uuid).returns(self.s3file)
            s3_tools.async_func('sign_url_from_do').call_with(
                s3_file=self.s3file,
                expire_secs=const.S3_EXPIRE_SECS,
                filename=self.filename,
                as_attachment=True,
            ).returns(self.url)

            result = await judge._sign_file_url(self.uuid, self.filename)

        self.assertEqual(result, self.result)
