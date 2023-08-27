"""
Wrapped context managers for aiosqlite3.

Note that pg default enables auto-commit.
If you don't want auto-commit, use `async with Connection.transaction(): ...`.
"""

from abc import abstractmethod
from datetime import datetime
import sqlite3

import aiosqlite

import exceptions as exc
import log

from . import base


async def open():
    aiosqlite.register_adapter(bool, int)
    aiosqlite.register_converter("BOOLEAN", lambda v: bool(int(v)))

    global _db
    if not _db:
        _db = await aiosqlite.connect(':memory:')

    return _db


async def close():
    global _db
    old_db = _db
    _db = None

    if old_db:
        await old_db.close()


_db: aiosqlite.Connection = None


class _SafeExecutor(base._SafeExecutor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # import re
        # self._sql = re.sub(r'\$\d+', r'?', self._sql)

    async def __aenter__(self) -> None | sqlite3.Row | list[sqlite3.Row]:
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

        global _db
        try:
            results = await self._exec(_db)
        except tuple(self._exception_mapping) as e:
            raise self._exception_mapping[type(e)] from e

        exec_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        log.info(f"Ended {self.__class__.__name__}: {self._event} after {exec_time_ms} ms")
        # util.metric.sql_time(self._event, exec_time_ms)

        if self._raise_not_found and not results:
            raise exc.persistence.NotFound

        return results

    @abstractmethod
    async def _exec(self, conn: aiosqlite.Connection):
        raise NotImplementedError

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._fetch == 'one' or self._fetch == 1 and exc_type is TypeError:  # Handles TypeError: value unpack
            raise exc.persistence.NotFound


class OnlyExecute(_SafeExecutor):
    def __init__(self, event: str, sql: str, parameters: dict = None,
                 **kwparams):
        super().__init__(event=event, sql=sql, parameters=parameters, fetch=None, raise_not_found=False,
                         **kwparams)

    async def _exec(self, conn: aiosqlite.Connection):
        await conn.execute(self._sql, self._parameters)

    async def __aenter__(self) -> None:
        await super().__aenter__()


class FetchOne(_SafeExecutor):
    def __init__(self, event: str, sql: str, parameters: dict = None,
                 **kwparams):
        super().__init__(event=event, sql=sql, parameters=parameters, fetch=1, raise_not_found=True,
                         **kwparams)

    async def _exec(self, conn: aiosqlite.Connection):
        async with conn.execute(self._sql, self._parameters) as cursor:
            cursor: aiosqlite.Cursor
            return await cursor.fetchone()

    async def __aenter__(self) -> sqlite3.Row:
        return await super().__aenter__()


class FetchAll(_SafeExecutor):
    def __init__(self, event: str, sql: str, parameters: dict = None, raise_not_found: bool = True,
                 **kwparams):
        super().__init__(event=event, sql=sql, parameters=parameters, fetch='all', raise_not_found=raise_not_found,
                         **kwparams)

    async def _exec(self, conn: aiosqlite.Connection):
        async with conn.execute(self._sql, self._parameters) as cursor:
            cursor: aiosqlite.Cursor
            return await cursor.fetchall()

    async def __aenter__(self) -> list[sqlite3.Row]:
        return await super().__aenter__()
