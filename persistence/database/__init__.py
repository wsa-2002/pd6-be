import aiomysql
from config import DBConfig


_pool: aiomysql.pool.Pool = None  # Need to be init/closed manually


async def initialize(db_config: DBConfig):
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            db=db_config.db_name,
        )


def close():
    global _pool
    if _pool is not None:
        _pool.close()


# For import usage
from . import (
    account,
    institute,
    rbac,
)
