"""
Wrapped context managers for aiosqlite3.
"""

import sqlite3

import aiosqlite

import exceptions as exc

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
        # log.info(f"Starting {self.__class__.__name__}: {self._event}, sql: {self._sql}, params: {self._parameters}")

        global _db
        try:
            results = await self._exec(_db)
        except tuple(self._exception_mapping) as e:
            raise self._exception_mapping[type(e)] from e

        if self._raise_not_found and not results:
            raise exc.persistence.NotFound

        return results


class OnlyExecute(_SafeExecutor):
    def __init__(self, event: str, sql: str, parameters: dict = None,
                 **kwparams):
        super().__init__(event=event, sql=sql, parameters=parameters, fetch=None, raise_not_found=False,
                         **kwparams)

    async def _exec(self, conn: aiosqlite.Connection):
        await conn.execute(self._sql, self._parameters)


class FetchOne(_SafeExecutor):
    def __init__(self, event: str, sql: str, parameters: dict = None,
                 **kwparams):
        super().__init__(event=event, sql=sql, parameters=parameters, fetch=1, raise_not_found=True,
                         **kwparams)

    async def _exec(self, conn: aiosqlite.Connection):
        async with conn.execute(self._sql, self._parameters) as cursor:
            cursor: aiosqlite.Cursor
            return await cursor.fetchone()


class FetchAll(_SafeExecutor):
    def __init__(self, event: str, sql: str, parameters: dict = None, raise_not_found: bool = True,
                 **kwparams):
        super().__init__(event=event, sql=sql, parameters=parameters, fetch='all', raise_not_found=raise_not_found,
                         **kwparams)

    async def _exec(self, conn: aiosqlite.Connection):
        async with conn.execute(self._sql, self._parameters) as cursor:
            cursor: aiosqlite.Cursor
            return await cursor.fetchall()
