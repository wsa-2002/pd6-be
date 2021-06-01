"""
Controls the connection / driver of database.
Use safe-execution classes to access database in-code.
"""


import asyncpg

from base import mcs
from config import DBConfig


class PoolHandler(metaclass=mcs.Singleton):
    def __init__(self):
        self._pool: asyncpg.pool.Pool = None  # Need to be init/closed manually

    async def initialize(self, db_config: DBConfig):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=db_config.host,
                port=db_config.port,
                user=db_config.username,
                password=db_config.password,
                database=db_config.db_name,
            )

    async def close(self):
        if self._pool is not None:
            await self._pool.close()

    @property
    def pool(self):
        return self._pool


pool_handler = PoolHandler()


# For import usage
from . import (
    account,
    institute,
    student_card,
    rbac,
    course,
    class_,
    team,
    challenge,
    problem,
    testdata,
)
