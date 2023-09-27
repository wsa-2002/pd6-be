import copy
import unittest
import uuid

from fastapi import UploadFile
import exceptions as exc

from base import enum, do
from util import mock, security

from . import team


class TestImportTeam(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.class_id = 1
        self.label = 'test'
        self.team_file = UploadFile(...)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_csv = controller.mock_module('service.csv')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(True)
            service_csv.async_func('import_team').call_with(
                mock.AnyInstanceOf(type(self.team_file.file)), class_id=self.class_id, label=self.label,
            ).returns(None)

            result = await mock.unwrap(team.import_team)(self.class_id, self.label, self.team_file)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, class_id=self.class_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.import_team)(self.class_id, self.label, self.team_file)


class TestGetTeamTemplateFile(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.s3_file = do.S3File(
            uuid=uuid.UUID('{12345678-1234-5678-1234-567812345678}'),
            bucket='bucket',
            key='key',
        )
        self.filename = 'team_template'
        self.result = team.GetTeamTemplateOutput(
            s3_file_uuid=self.s3_file.uuid,
            filename=self.filename,
        )

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            service_csv = controller.mock_module('service.csv')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(True)
            service_csv.async_func('get_team_template').call_with().returns((self.s3_file, self.filename))

            result = await mock.unwrap(team.get_team_template_file)()

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_system').call_with(
                context.account.id, enum.RoleType.normal,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.get_team_template_file)()


class TestReadTeam(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.team_id = 1
        self.team = do.Team(
            id=self.team_id,
            name='test',
            class_id=1,
            label='test',
            is_deleted=False,
        )
        self.result = copy.deepcopy(self.team)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, team_id=self.team_id,
            ).returns(True)

            db_team.async_func('read').call_with(self.team_id).returns(self.team)

            result = await mock.unwrap(team.read_team)(self.team_id)

        self.assertEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, team_id=self.team_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.read_team)(self.team_id)


class TestEditTeam(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.team_id = 1
        self.data = team.EditTeamInput(
            name='test',
            class_id=1,
            label='test',
        )

    async def test_happy_flow_class_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(True)
            service_rbac.async_func('validate_team').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)
            db_team.async_func('edit').call_with(
                team_id=self.team_id,
                name=self.data.name,
                class_id=self.data.class_id,
                label=self.data.label,
            ).returns(None)

            result = await mock.unwrap(team.edit_team)(self.team_id, self.data)

        self.assertIsNone(result)

    async def test_happy_flow_team_manager(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)
            service_rbac.async_func('validate_team').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(True)
            db_team.async_func('edit').call_with(
                team_id=self.team_id,
                name=self.data.name,
                class_id=self.data.class_id,
                label=self.data.label,
            ).returns(None)

            result = await mock.unwrap(team.edit_team)(self.team_id, self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)
            service_rbac.async_func('validate_team').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.edit_team)(self.team_id, self.data)


class TestDeleteTeam(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.team_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(True)

            db_team.async_func('delete').call_with(self.team_id).returns(None)

            result = await mock.unwrap(team.delete_team)(self.team_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.delete_team)(self.team_id)


class TestBrowseTeamAllMember(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.team_id = 1
        self.team_members = [
            do.TeamMember(
                member_id=1,
                team_id=self.team_id,
                role=enum.RoleType.normal,
            ),
            do.TeamMember(
                member_id=2,
                team_id=self.team_id,
                role=enum.RoleType.normal,
            )
        ]
        self.result = copy.deepcopy(self.team_members)

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, team_id=self.team_id,
            ).returns(True)

            db_team.async_func('browse_members').call_with(team_id=self.team_id).returns(self.team_members)

            result = await mock.unwrap(team.browse_team_all_member)(self.team_id)

        self.assertCountEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.normal, team_id=self.team_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.browse_team_all_member)(self.team_id)


class TestAddTeamMember(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.team_id = 1
        self.data = [
            team.AddMemberInput(
                account_referral='test1',
                role=enum.RoleType.normal,
            ),
            team.AddMemberInput(
                account_referral='test2',
                role=enum.RoleType.normal,
            ),
        ]
        self.result = [True for _ in self.data]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(True)

            db_team.async_func('add_members').call_with(
                team_id=self.team_id,
                member_roles=[(member.account_referral, member.role)
                              for member in self.data],
            ).returns(self.result)

            result = await mock.unwrap(team.add_team_member)(self.team_id, self.data)

        self.assertCountEqual(result, self.result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.add_team_member)(self.team_id, self.data)


class TestEditTeamMember(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.team_id = 1
        self.data = [
            team.EditMemberInput(
                member_id=1,
                role=enum.RoleType.normal,
            ),
            team.EditMemberInput(
                member_id=2,
                role=enum.RoleType.normal,
            ),
        ]

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(True)

            for member in self.data:
                db_team.async_func('edit_member').call_with(
                    team_id=self.team_id,
                    member_id=member.member_id,
                    role=member.role,
                ).returns(None)

            result = await mock.unwrap(team.edit_team_member)(self.team_id, self.data)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.edit_team_member)(self.team_id, self.data)


class TestDeleteTeamMember(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.login_account = security.AuthedAccount(id=1, cached_username='self')
        self.team_id = 1
        self.member_id = 1

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')
            db_team = controller.mock_module('persistence.database.team')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(True)

            db_team.async_func('delete_member').call_with(team_id=self.team_id, member_id=self.member_id).returns(None)

            result = await mock.unwrap(team.delete_team_member)(self.team_id, self.member_id)

        self.assertIsNone(result)

    async def test_no_permission(self):
        with (
            mock.Controller() as controller,
            mock.Context() as context,
        ):
            context.set_account(self.login_account)

            service_rbac = controller.mock_module('service.rbac')

            service_rbac.async_func('validate_class').call_with(
                context.account.id, enum.RoleType.manager, team_id=self.team_id,
            ).returns(False)

            with self.assertRaises(exc.NoPermission):
                await mock.unwrap(team.delete_team_member)(self.team_id, self.member_id)
