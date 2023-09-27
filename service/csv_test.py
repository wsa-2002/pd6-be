import csv as py_csv
from datetime import datetime
import io
import unittest
from uuid import UUID

import exceptions as exc
from base import enum, do
from util import mock

from . import csv


class TestGetAccountTemplate(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )

        self.expected_happy_flow_result = (self.s3_file, csv.ACCOUNT_TEMPLATE_FILENAME)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            s3_temp = controller.mock_module('persistence.s3.temp')
            s3_temp.async_func('upload').call_with(
                file=mock.AnyInstanceOf(io.BytesIO),
            ).returns(self.s3_file)

            result = await csv.get_account_template()

        self.assertEqual(result, self.expected_happy_flow_result)


class TestImportAccount(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.account_file = io.BytesIO(b'account')
        self.generator = (test for test in [1, 2, ])
        self.rows = py_csv.DictReader(io.StringIO(
            ("RealName,Username,Password,AlternativeEmail,Nickname\n"
             "real,user,password,alter,nick\n"
             "real2,user2,password2,alter2,nick2")
        ))
        self.rows_uncompleted = py_csv.DictReader(io.StringIO(
            ("RealName,Username,Password,AlternativeEmail,Nickname\n"
             "real,,password,alter,nick\n"
             "real2,user2,password2,alter2,nick2")
        ))
        self.rows_loss_alternative_email = py_csv.DictReader(io.StringIO(
            ("RealName,Username,Password,AlternativeEmail,Nickname\n"
             "real,user,password,,nick\n"
             "real2,user2,password2,,nick2")
        ))
        self.rows_loss_header = py_csv.DictReader(io.StringIO(
            ("RealName,,Password,AlternativeEmail,Nickname\n"
             "real,,password,alter,nick\n"
             "real2,user2,password2,alter2,nick2")
        ))
        self.data = [
            ('real', 'user', 'password-hash', 'alter', 'nick'),
            ('real2', 'user2', 'password2-hash', 'alter2', 'nick2'),
        ]
        self.data_loss_alternative_email = [
            ('real', 'user', 'password-hash', '', 'nick'),
            ('real2', 'user2', 'password2-hash', '', 'nick2'),
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            util_security = controller.mock_module('util.security')

            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.account_file)), 'utf_8_sig',
            ).returns(self.generator)
            controller.mock_global_func('csv.DictReader').call_with(
                mock.AnyInstanceOf(type(self.generator)),
            ).returns(self.rows)
            util_security.func('hash_password').call_with(
                'password',
            ).returns('password' + '-hash')
            util_security.func('hash_password').call_with(
                'password2',
            ).returns('password2' + '-hash')

            db_account.async_func('batch_add_normal').call_with(
                self.data,
            ).returns(None)

            result = await csv.import_account(self.account_file)

        self.assertIsNone(result)

    async def test_happy_flow_loss_alternative_email(self):
        with (
            mock.Controller() as controller,
        ):
            db_account = controller.mock_module('persistence.database.account')
            util_security = controller.mock_module('util.security')

            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.account_file)), 'utf_8_sig',
            ).returns(self.generator)
            controller.mock_global_func('csv.DictReader').call_with(
                mock.AnyInstanceOf(type(self.generator)),
            ).returns(self.rows_loss_alternative_email)
            util_security.func('hash_password').call_with(
                'password',
            ).returns('password' + '-hash')
            util_security.func('hash_password').call_with(
                'password2',
            ).returns('password2' + '-hash')

            db_account.async_func('batch_add_normal').call_with(
                self.data_loss_alternative_email,
            ).returns(None)

            result = await csv.import_account(self.account_file)

        self.assertIsNone(result)

    async def test_data_uncompleted(self):
        with (
            mock.Controller() as controller,
        ):
            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.account_file)), 'utf_8_sig',
            ).returns(self.generator)
            controller.mock_global_func('csv.DictReader').call_with(
                mock.AnyInstanceOf(type(self.generator)),
            ).returns(self.rows_uncompleted)

            with self.assertRaises(exc.IllegalInput):
                await csv.import_account(self.account_file)

    async def test_loss_header(self):
        with (
            mock.Controller() as controller,
        ):
            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.account_file)), 'utf_8_sig',
            ).returns(self.generator)
            controller.mock_global_func('csv.DictReader').call_with(
                mock.AnyInstanceOf(type(self.generator)),
            ).returns(self.rows_loss_header)

            with self.assertRaises(exc.IllegalInput):
                await csv.import_account(self.account_file)

    async def test_unicode_decode_error(self):
        with (
            mock.Controller() as controller,
        ):
            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.account_file)), 'utf_8_sig',
            ).raises(UnicodeDecodeError('unicode', b'\x00\x00', 1, 2, 'Error'))

            with self.assertRaises(exc.FileDecodeError):
                await csv.import_account(self.account_file)


class TestGetTeamTemplate(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )

        self.expected_happy_flow_result = (self.s3_file, csv.TEAM_TEMPLATE_FILENAME)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            s3_temp = controller.mock_module('persistence.s3.temp')
            s3_temp.async_func('upload').call_with(
                file=mock.AnyInstanceOf(io.BytesIO),
            ).returns(self.s3_file)

            result = await csv.get_team_template()

        self.assertEqual(result, self.expected_happy_flow_result)


class TestImportTeam(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.team_file = io.BytesIO(b'team')
        self.class_id = 1
        self.label = 'label'

        self.generator = (test for test in [1, 2, ])
        self.rows = py_csv.DictReader(io.StringIO(
            "TeamName,Manager,Member 2,Member 3,Member 4,Member 5,Member 6,Member 7,Member 8,Member 9,Member 10\n"
            "team,manager,member2,member3,member4,member5,member6,member7,member8,member9,\n"
            "team2,manager2,member2,member3,member4,,member6,member7,member8,member9,member10"
        ))
        self.rows_loss_header = py_csv.DictReader(io.StringIO(
            "TeamName,Manager,Member 2,Member 3,Member 4,Member 5,Member 6,Member 7,,Member 9,Member 10\n"
            "team,manager,member2,member3,member4,member5,member6,member7,member8,member9,\n"
            "team2,manager2,member2,member3,member4,,member6,member7,member8,member9,member10"
        ))
        self.data = [
            ('team', [
                ('manager', enum.RoleType.manager), ('member2', enum.RoleType.normal),
                ('member3', enum.RoleType.normal), ('member4', enum.RoleType.normal),
                ('member5', enum.RoleType.normal), ('member6', enum.RoleType.normal),
                ('member7', enum.RoleType.normal), ('member8', enum.RoleType.normal),
                ('member9', enum.RoleType.normal),
            ]),
            ('team2', [
                ('manager2', enum.RoleType.manager), ('member2', enum.RoleType.normal),
                ('member3', enum.RoleType.normal), ('member4', enum.RoleType.normal),
                ('member6', enum.RoleType.normal), ('member7', enum.RoleType.normal),
                ('member8', enum.RoleType.normal), ('member9', enum.RoleType.normal),
                ('member10', enum.RoleType.normal),
            ]),
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_team = controller.mock_module('persistence.database.team')

            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.team_file)), 'utf_8_sig',
            ).returns(self.generator)
            controller.mock_global_func('csv.DictReader').call_with(
                mock.AnyInstanceOf(type(self.generator)),
            ).returns(self.rows)

            db_team.async_func('add_team_and_add_member').call_with(
                class_id=self.class_id, team_label=self.label, datas=self.data,
            ).returns(None)

            result = await csv.import_team(self.team_file, self.class_id, self.label)

        self.assertIsNone(result)

    async def test_loss_header(self):
        with (
            mock.Controller() as controller,
        ):
            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.team_file)), 'utf_8_sig',
            ).returns(self.generator)
            controller.mock_global_func('csv.DictReader').call_with(
                mock.AnyInstanceOf(type(self.generator)),
            ).returns(self.rows_loss_header)

            with self.assertRaises(exc.IllegalInput):
                await csv.import_team(self.team_file, self.class_id, self.label)

    async def test_unicode_decode_error(self):
        with (
            mock.Controller() as controller,
        ):
            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.team_file)), 'utf_8_sig',
            ).raises(UnicodeDecodeError('unicode', b'\x00\x00', 1, 2, 'Error'))

            with self.assertRaises(exc.FileDecodeError):
                await csv.import_team(self.team_file, self.class_id, self.label)


class TestImportClassGrade(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.grade_file = io.BytesIO(b'team')
        self.title = 'title'
        self.class_id = 1
        self.update_time = datetime(2023, 7, 19, 12)

        self.generator = (test for test in [1, 2, ])
        self.rows = py_csv.DictReader(io.StringIO(
            "Receiver,Score,Comment,Grader\n"
            "receiver,100,comment,grader\n"
            "receiver2,100,comment2,grader2"
        ))
        self.data = [
            ('receiver', '100', 'comment', 'grader'),
            ('receiver2', '100', 'comment2', 'grader2'),
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            db_grade = controller.mock_module('persistence.database.grade')

            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.grade_file)), 'utf_8_sig',
            ).returns(self.generator)
            controller.mock_global_func('csv.DictReader').call_with(
                mock.AnyInstanceOf(type(self.generator)),

            ).returns(self.rows)

            db_grade.async_func('batch_add').call_with(
                class_id=self.class_id, title=self.title,
                grades=self.data, update_time=self.update_time,
            ).returns(None)

            result = await csv.import_class_grade(self.grade_file, self.title, self.class_id, self.update_time)

        self.assertIsNone(result)

    async def test_unicode_decode_error(self):
        with (
            mock.Controller() as controller,
        ):
            controller.mock_global_func('codecs.iterdecode').call_with(
                mock.AnyInstanceOf(type(self.grade_file)), 'utf_8_sig',
            ).raises(UnicodeDecodeError('unicode', b'\x00\x00', 1, 2, 'Error'))

            with self.assertRaises(exc.FileDecodeError):
                await csv.import_class_grade(self.grade_file, self.title, self.class_id, self.update_time)


class TestGetGradeTemplate(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.s3_file = do.S3File(
            uuid=UUID('d8ec7a6a-27e1-4cee-8229-4304ef933544'),
            bucket="bucket",
            key="key",
        )

        self.expected_happy_flow_result = (self.s3_file, csv.GRADE_TEMPLATE_FILENAME)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            s3_temp = controller.mock_module('persistence.s3.temp')
            s3_temp.async_func('upload').call_with(
                file=mock.AnyInstanceOf(io.BytesIO),
            ).returns(self.s3_file)

            result = await csv.get_grade_template()

        self.assertEqual(result, self.expected_happy_flow_result)
