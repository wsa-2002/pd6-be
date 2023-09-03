import unittest

from base import do, enum
from util import mock

from . import account, base_mock


class TestBase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = await base_mock.open()

        await self.db.execute('''
create table account
(
    id                serial                primary key,
    username          varchar               not null,
    pass_hash         varchar               not null,
    nickname          varchar               not null,
    real_name         varchar               not null,
    role              varchar               not null,
    alternative_email varchar,
    is_deleted        boolean default false not null,
    is_4s_hash        boolean default false not null
);
''')

    async def asyncTearDown(self):
        await base_mock.close()


class TestRead(TestBase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        await self.db.execute('''
INSERT INTO account VALUES (1, 'admin', '$argon2id$v=19$m=102400,t=2,p=8$gbA2Ziyl9H5vLWXMeQ/hvA$oEjG4MX+m9yyezM42ialUg', 'admin', 'admin', 'MANAGER', 'test@gmail.com', false, false); -- password: admin
''')

    async def test_happy_flow(self):
        with (
            mock.Controller() as controller,
        ):
            controller.mock_global_class('persistence.database.account.FetchOne', base_mock.FetchOne)

            result = await account.read(1)

        self.assertEqual(result, do.Account(1, 'admin', 'admin', 'admin', enum.RoleType.manager, False, alternative_email='test@gmail.com'))
