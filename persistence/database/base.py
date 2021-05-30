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

import exceptions as exc

from . import pool_handler


# Context managers for safe execution


class SafeConnection:
    """
    This class returns the RAW connection of used database package.
    Usage should follow the database package's documentations.

    Note that asyncpg does not support keyword-bounded arguments; only positional arguments are allowed.
    """
    def __init__(self, event: str):
        # self._start_time = datetime.now()
        self._event = event
        self._conn: asyncpg.connection.Connection = None  # acquire in __aenter__

    async def __aenter__(self) -> asyncpg.connection.Connection:
        self._conn: asyncpg.connection.Connection = await pool_handler.pool.acquire()
        # log.info(f"Starting {self.__class__.__name__}: {self._event}")
        return self._conn

    async def __aexit__(self, exc_type, exc_value, traceback):
        await pool_handler.pool.release(self._conn)
        # log.info(f"Ended {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}")


class SafeExecutor:
    def __init__(self, event: str, sql: str, parameters: Dict = None, fetch=None, **kwparams):
        """
        A safe execution context manager to open, execute, fetch, and close connections automatically.
        It also binds named parameters with `sql=r'%(key)s', key=value` since asyncpg does not support that.

        :param parameters: named parameters to be bind in given sql, can also be given through **params;
                           parameters should be bounded in sql with syntax "%(key)s"
        :param fetch: 'one', 1, 'all', an integer (maxsize for many), or None (don't fetch; returns cursor)
        """
        # self._start_time = datetime.now()
        self._event = event
        self._fetch = fetch

        # Handle keyword arguments
        if parameters is None:
            parameters = {}
        parameters.update(kwparams)
        # Convert to asyncpg position-based arguments because asyncpg does not support that
        self._sql, self._parameters = pyformat2psql(sql, parameters)

    async def __aenter__(self) -> Optional[Union[asyncpg.Record, List[asyncpg.Record]]]:
        """
        If fetch is 1 / "one": return a tuple (= row)

        If fetch is "many" or "all": return a list of tuples (= rows)

        If fetch is `None` or strange value: return `None`
        """
        # log.info(f"Starting {self.__class__.__name__}: {self._event}, sql: {self._sql}, params: {self._parameters}")

        async with pool_handler.pool.acquire() as conn:
            conn: asyncpg.connection.Connection

            if not self._fetch:
                await conn.execute(self._sql, *self._parameters)
                return

            if self._fetch == 'all':
                results = await conn.fetch(self._sql, *self._parameters)
            elif self._fetch == 'one' or self._fetch == 1:
                results = await conn.fetchrow(self._sql, *self._parameters)
            elif isinstance(self._fetch, int) and self._fetch > 0:
                cur = await conn.cursor(self._sql, *self._parameters)
                results = await cur.fetch(self._fetch)
            else:
                raise ValueError

            if not results:
                raise exc.NotFound

            return results

            # log.info(f"Ended {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}")

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._fetch == 'one' or self._fetch == 1 and exc_type is TypeError:  # Handles TypeError: value unpack
            raise exc.NotFound
