"""
Wrapped context managers for asyncpg.

Note that pg default enables auto-commit.
If you don't want auto-commit, use `async with Connection.transaction(): ...`.
"""


import collections
from datetime import datetime
import itertools
from typing import Any, Dict, Tuple, List, Optional, Union

import log


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
import asyncpg.exceptions
import asyncpg.transaction

import exceptions as exc

import util.metric

from . import pool_handler


# Context managers for safe execution


class SafeConnection:
    """
    This class returns the RAW connection of used database package.
    Usage should follow the database package's documentations.

    Note that asyncpg does not support keyword-bounded arguments; only positional arguments are allowed.
    """
    def __init__(self, event: str, auto_transaction: bool):
        self._start_time = datetime.now()
        self._event = event
        self._conn: asyncpg.connection.Connection = None  # acquire in __aenter__
        self._auto_transaction = auto_transaction
        self._transaction: asyncpg.transaction.Transaction = None  # acquire in __aenter__

    async def __aenter__(self) -> asyncpg.connection.Connection:
        self._conn: asyncpg.connection.Connection = await pool_handler.pool.acquire()
        log.info(f"Starting {self.__class__.__name__}: {self._event}")
        if self._auto_transaction:
            self._transaction = self._conn.transaction()
            await self._transaction.__aenter__()
        return self._conn

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._auto_transaction:
            await self._transaction.__aexit__(exc_type, exc_value, traceback)

        await pool_handler.pool.release(self._conn)
        exec_time_ms = (datetime.now() - self._start_time).total_seconds() * 1000
        log.info(f"Ended {self.__class__.__name__}: {self._event} after {exec_time_ms} ms")
        util.metric.sql_time(self._event, exec_time_ms)


class SafeExecutor:
    def __init__(self, event: str, sql: str, parameters: Dict = None,
                 fetch: Union[int, str, None] = None, raise_not_found: bool = True,
                 **kwparams):
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
        self._raise_not_found = raise_not_found

        # Handle keyword arguments
        if parameters is None:
            parameters = {}
        parameters.update(kwparams)
        # Convert to asyncpg position-based arguments because asyncpg does not support that
        self._sql, self._parameters = pyformat2psql(sql, parameters)

    async def __aenter__(self) -> Optional[Union[asyncpg.Record, List[asyncpg.Record]]]:
        """
        If fetch
            - == 1: return a tuple (= row)
            - > 1: return a list of tuples (= rows) with len <= fetch
            - == "all": return a list of tuples (= rows) with all records
            - is `None` or any false value: return None (no fetch)
            - strange value: raise ValueError

        Will raise NotFound if requested to fetch but unable to fetch anything.
        """
        start_time = datetime.now()

        log.info(f"Starting {self.__class__.__name__}: {self._event}, sql: {self._sql}, params: {self._parameters}")

        async with pool_handler.pool.acquire() as conn:
            try:
                results = await self._exec(conn)
            except asyncpg.exceptions.UniqueViolationError as e:
                raise exc.persistence.UniqueViolationError(cause=e)

        exec_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        log.info(f"Ended {self.__class__.__name__}: {self._event} after {exec_time_ms} ms")
        util.metric.sql_time(self._event, exec_time_ms)

        if self._fetch and not results and self._raise_not_found:
            raise exc.persistence.NotFound

        return results

    async def _exec(self, conn: asyncpg.connection.Connection):
        if not self._fetch:
            await conn.execute(self._sql, *self._parameters)
            return None

        if isinstance(self._fetch, int):
            if self._fetch == 1:
                return await conn.fetchrow(self._sql, *self._parameters)
            if self._fetch > 1:
                cur = await conn.cursor(self._sql, *self._parameters)
                return await cur.fetch(self._fetch)

        if isinstance(self._fetch, str):
            if self._fetch == 'all':
                return await conn.fetch(self._sql, *self._parameters)

        raise ValueError

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._fetch == 'one' or self._fetch == 1 and exc_type is TypeError:  # Handles TypeError: value unpack
            raise exc.persistence.NotFound
