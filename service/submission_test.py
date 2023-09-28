from datetime import datetime
import io
import unittest
from uuid import UUID

from base import do
from util import mock

from . import submission


class TestSubmit(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.file = io.BytesIO(b'file')
        self.filename = 'filename'
        self.account_id = 1
        self.problem_id = 1
        self.language_id = 1
        self.file_length = 0
        self.submit_time = datetime(2023, 7, 29, 12)

        self.submission_id = 1
        self.file_uuid = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')
        self.content_file_uuid = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )

        self.expected_happy_flow_result = self.submission_id

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            s3_submission = controller.mock_module('persistence.s3.submission')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_submission = controller.mock_module('persistence.database.submission')

            controller.mock_global_func('uuid.uuid4').call_with().returns(
                self.file_uuid,
            )
            s3_submission.async_func('upload').call_with(
                mock.AnyInstanceOf(type(self.file)), file_uuid=self.file_uuid,
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(
                s3_file=self.s3_file,
            ).returns(self.content_file_uuid)
            db_submission.async_func('add').call_with(
                account_id=self.account_id, problem_id=self.problem_id, language_id=self.language_id,
                content_file_uuid=self.content_file_uuid, content_length=self.file_length,
                filename=self.filename, submit_time=self.submit_time,
            ).returns(self.submission_id)

            result = await submission.submit(self.file, self.filename, self.account_id, self.problem_id,
                                             self.language_id, self.file_length, self.submit_time)

        self.assertEqual(result, self.expected_happy_flow_result)


class TestSubmitEssay(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.file = io.BytesIO(b'file')
        self.filename = 'filename'
        self.account_id = 1
        self.essay_id = 1
        self.submit_time = datetime(2023, 7, 29, 12)

        self.essay_submission_id = 1
        self.file_uuid = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')
        self.content_file_uuid = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )

        self.expected_happy_flow_result = self.essay_submission_id

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            s3_essay_submission = controller.mock_module('persistence.s3.essay_submission')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')

            controller.mock_global_func('uuid.uuid4').call_with().returns(
                self.file_uuid,
            )
            s3_essay_submission.async_func('upload').call_with(
                mock.AnyInstanceOf(type(self.file)), file_uuid=self.file_uuid,
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(
                s3_file=self.s3_file,
            ).returns(self.content_file_uuid)
            db_essay_submission.async_func('add').call_with(
                account_id=self.account_id, essay_id=self.essay_id,
                content_file_uuid=self.content_file_uuid,
                filename=self.filename, submit_time=self.submit_time,
            ).returns(self.essay_submission_id)

            result = await submission.submit_essay(self.file, self.filename, self.account_id,
                                                   self.essay_id, self.submit_time)

        self.assertEqual(result, self.expected_happy_flow_result)


class TestResubmitEssay(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.file = io.BytesIO(b'file')
        self.filename = 'filename'
        self.essay_submission_id = 1
        self.submit_time = datetime(2023, 7, 29, 12)

        self.file_uuid = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')
        self.content_file_uuid = UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544')
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            s3_essay_submission = controller.mock_module('persistence.s3.essay_submission')
            db_s3_file = controller.mock_module('persistence.database.s3_file')
            db_essay_submission = controller.mock_module('persistence.database.essay_submission')

            controller.mock_global_func('uuid.uuid4').call_with().returns(
                self.file_uuid,
            )
            s3_essay_submission.async_func('upload').call_with(
                mock.AnyInstanceOf(type(self.file)), file_uuid=self.file_uuid,
            ).returns(self.s3_file)
            db_s3_file.async_func('add_with_do').call_with(
                s3_file=self.s3_file,
            ).returns(self.content_file_uuid)
            db_essay_submission.async_func('edit').call_with(
                essay_submission_id=self.essay_submission_id,
                content_file_uuid=self.content_file_uuid,
                filename=self.filename, submit_time=self.submit_time,
            ).returns(None)

            result = await submission.resubmit_essay(self.file, self.filename,
                                                     self.essay_submission_id, self.submit_time)

        self.assertIsNone(result)
