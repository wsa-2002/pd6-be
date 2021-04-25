import asyncpg
from config import DBConfig


_pool: asyncpg.pool.Pool = None  # Need to be init/closed manually


async def initialize(db_config: DBConfig):
    global _pool
    if _pool is None:
        _pool = asyncpg.create_pool(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            database=db_config.db_name,
        )


async def close():
    global _pool
    if _pool is not None:
        await _pool.close()


# For import usage
from . import (
    account,
    institute,
    student_card,
    rbac,
)
