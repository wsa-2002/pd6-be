"""
Controls the connection / driver of database.
Use safe-execution classes to access database in-code.

------

分類的邏輯：拿出來的東西是什麼，就放在哪個檔案
e.g. 用 account_id 拿 submissions -> submission.browse(account_id=1)
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
                max_size=db_config.max_pool_size,
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
    account_vo,
    institute,
    student_card,
    email_verification,
    rbac,

    course,
    class_,
    class_vo,
    team,
    grade,
    challenge,

    problem,
    problem_judge_setting_customized,
    problem_reviser_settings,

    testcase,
    submission,
    judgment,
    judge_case,
    essay,
    essay_submission,
    s3_file,

    assisting_data,

    peer_review,
    peer_review_record,

    scoreboard,
    scoreboard_setting_team_project,
    scoreboard_setting_team_contest,

    announcement,
    access_log,

    view,
)
