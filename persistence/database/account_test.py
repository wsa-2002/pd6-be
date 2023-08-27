import unittest

from util import mock

from . import account
from . import base_mock


class TestBase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = await base_mock.MockDB().__aenter__()

        await self.db.execute('''
create table account
(
    id                serial
        primary key,
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
        await self.db.__aexit__(None, None, None)


class TestRead(TestBase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        await self.db.execute('''
INSERT INTO account VALUES (1, 'admin', '$argon2id$v=19$m=102400,t=2,p=8$gbA2Ziyl9H5vLWXMeQ/hvA$oEjG4MX+m9yyezM42ialUg', 'admin', 'admin', 'MANAGER', 'test@gmail.com', false, false); -- password: admin
''')

    async def test_happy_flow(self):
        from unittest import mock as utmock
        with (
            mock.Controller() as controller,
        ):
            from unittest.mock import patch

            def create(*args, **kwargs):
                cls, args = args[0], args[1:]
                return base_mock.FetchOne(*args, **kwargs)

            with patch('persistence.database.account.FetchOne.__new__', wraps=create) as aa:

                result = await account.read(1)

        from base import do, enum
        self.assertEqual(result, do.Account(1, 'admin', 'admin', 'admin', enum.RoleType.manager, False, alternative_email='test@gmail.com'))
