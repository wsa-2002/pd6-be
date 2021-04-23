from typing import Any

import aiomysql
import aiomysql.log


class Cursor(aiomysql.cursors.Cursor):
    async def execute(self, query, args=None, **kwargs):
        """Executes the given operation

        Executes the given operation substituting any markers with
        the given parameters.

        For example, getting all rows where id is 5:
          cursor.execute("SELECT * FROM t1 WHERE id = %s", (5,))

        :param query: ``str`` sql statement
        :param args: ``tuple`` or ``list`` of arguments for sql query
        :returns: ``int``, number of rows that has been produced of affected
        """
        conn = self._get_db()

        while (await self.nextset()):
            pass

        if kwargs and args:
            if not isinstance(args, dict):
                raise TypeError("Cannot have kwargs and positional args at the same time")
            args = args.copy()
            args.update(kwargs)

        if args is not None:
            query = query % self._escape_args(args, conn)

        await self._query(query)
        self._executed = query
        if self._echo:
            aiomysql.log.logger.info(query)
            aiomysql.log.logger.info("%r", args)
        return self._rowcount


# Context managers for safe execution


class SafeConnection:
    def __init__(self, event: str, autocommit=False):
        # self._start_time = datetime.now()
        self._event = event
        global _pool
        self._pool: aiomysql.pool.Pool = _pool
        self._conn: aiomysql.connection.Connection = None  # acquire in __aenter__
        self._autocommit = autocommit

    async def __aenter__(self) -> aiomysql.connection.Connection:
        self._conn = await self._pool.acquire()
        await self._conn.autocommit(self._autocommit)
        # log.info(f"Starting {self.__class__.__name__}: {self._event}")
        return self._conn

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._pool.release(self._conn)
        # log.info(f"Ended {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}")


class SafeCursor:
    def __init__(self, event: str, autocommit=False):
        # self._start_time = datetime.now()
        self._event = event
        global _pool
        self._pool: aiomysql.pool.Pool = _pool
        self._conn: aiomysql.connection.Connection = None  # acquire in __aenter__
        self._autocommit = autocommit
        self._cursor: aiomysql.cursors.Cursor = None  # acquire in __aenter__

    async def __aenter__(self) -> aiomysql.cursors.Cursor:
        self._conn = await self._pool.acquire()
        await self._conn.autocommit(self._autocommit)
        self._cursor = await self._conn.cursor()
        # log.info(f"Starting {self.__class__.__name__}: {self._event}")
        return self._cursor

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._cursor.close()
        self._pool.release(self._conn)
        # log.info(f"Ended {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}")


class SafeExecutor:
    def __init__(self, event: str, sql: str, parameters=None, commit=False, fetch=None, **params):
        """
        Bind named parameters with `sql=r'%(key)s', key=value`

        :param fetch: 'one', 1, 'all', an integer (maxsize for many), or None (don't fetch)
        """
        # self._start_time = datetime.now()
        self._event = event
        global _pool
        self._pool: aiomysql.pool.Pool = _pool
        self._conn: aiomysql.connection.Connection = None  # acquire in __aenter__
        self._commit = commit
        self._cursor: aiomysql.cursors.Cursor = None  # acquire in __aenter__
        self._sql = sql
        self._parameters = parameters or {}
        self._fetch = fetch
        if params:
            self._parameters.update(params)

    async def __aenter__(self) -> Any:
        """
        If fetch 1 / one: return a tuple (= row)

        If fetch many or all: return a list of tuples (= rows)

        If fetch `None` or strange value: return `None`
        """
        # log.info(f"Starting {self.__class__.__name__}: {self._event}, sql: {self._sql}, params: {self._parameters}")
        self._conn = await self._pool.acquire()
        self._cursor = await self._conn.cursor()
        try:
            await self._cursor.execute(self._sql, self._parameters)
        except Exception as e:
            raise e
        else:
            # log.info(f"Executed {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}, "
            #          f"sql: {self._sql}")
            if self._fetch == 'one' or self._fetch == 1:
                return await self._cursor.fetchone()

            if self._fetch == 'all':
                return await self._cursor.fetchall()

            if isinstance(self._fetch, int) and self._fetch > 0:
                return await self._cursor.fetchmany(self._fetch)

            return None  # got strange things or None for fetch

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._cursor.close()
        if self._commit:
            await self._conn.commit()
        self._pool.release(self._conn)
        # log.info(f"Ended {self.__class__.__name__}: {self._event} after {datetime.now() - self._start_time}")
