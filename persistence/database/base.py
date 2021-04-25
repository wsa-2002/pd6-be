"""
Wrapped context managers for asyncpg.

Note that pg default enables auto-commit.
If you don't want auto-commit, use `async with Connection.transaction(): ...`.
"""


import collections
import itertools
from typing import Any, Dict, Tuple, List, Optional, Union


# https://github.com/MagicStack/asyncpg/issues/9#issuecomment-600659015
def pyformat2psql(query: str, named_args: Dict[str, Any]) -> Tuple[str, List[Any]]:
    positional_generator = itertools.count(1)
    positional_map = collections.defaultdict(lambda: '${}'.format(next(positional_generator)))
    formatted_query = query % positional_map
    positional_items = sorted(
        positional_map.items(),
        key=lambda item: int(item[1].replace('$', '')),
    )
    positional_args = [named_args[named_arg] for named_arg, _ in positional_items]
    return formatted_query, positional_args


from typing import Dict

import asyncpg

from . import _pool


# Context managers for safe execution


class SafeConnection:
    def __init__(self, event: str):
        # self._start_time = datetime.now()
        self._event = event
        self._pool: asyncpg.pool.Pool = _pool
        self._conn: asyncpg.connection.Connection = None  # acquire in __aenter__

    async def __aenter__(self) -> asyncpg.connection.Connection:
        self._conn: asyncpg.connection.Connection = await self._pool.acquire()
        # log.info(f"Starting {self.__class__.__name__}: {self._event}")
        return self._conn

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._pool.release(self._conn)
        # log.info(f"Ended {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}")


class SafeExecutor:
    def __init__(self, event: str, sql: str, parameters: Dict = None, fetch=None, **kwparams):
        """
        Bind named parameters with `sql=r'%(key)s', key=value`

        :param parameters: named parameters to be bind in given sql, can also be given through **params;
                           parameters should be bounded in sql with syntax "%(key)s"
        :param fetch: 'one', 1, 'all', an integer (maxsize for many), or None (don't fetch; returns cursor)
        """
        # self._start_time = datetime.now()
        self._event = event
        self._pool: asyncpg.pool.Pool = _pool
        self._fetch = fetch

        # Handle keyword arguments
        if parameters is None:
            parameters = {}
        parameters.update(kwparams)
        # Convert to asyncpg position-based arguments
        self._sql, self._parameters = pyformat2psql(sql, parameters)

    async def __aenter__(self) -> Optional[Union[asyncpg.Record, List[asyncpg.Record]]]:
        """
        If fetch 1 / one: return a tuple (= row)

        If fetch many or all: return a list of tuples (= rows)

        If fetch `None` or strange value: return `None`
        """
        # log.info(f"Starting {self.__class__.__name__}: {self._event}, sql: {self._sql}, params: {self._parameters}")

        async with self._pool.acquire() as conn:
            conn: asyncpg.connection.Connection

            if self._fetch == 'all':
                return await conn.fetch(self._sql, *self._parameters)

            elif self._fetch == 'one' or self._fetch == 1:
                return await conn.fetchrow(self._sql, *self._parameters)

            elif isinstance(self._fetch, int) and self._fetch > 0:
                cur = await conn.cursor(self._sql, *self._parameters)
                return await cur.fetch(self._fetch)

            else:
                await conn.execute(self._sql, *self._parameters)
                return None

            # log.info(f"Ended {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}")

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
