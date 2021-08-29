from typing import Sequence

from base import do
from base.popo import Filter, Sorter

from .base import SafeExecutor, SafeConnection
from .util import execute_count, compile_filters


async def add(account_id: int, institute_id: int, student_id: str, email: str) \
        -> int:
    async with SafeConnection(event='insert student card') as conn:
        async with conn.transaction():
            await conn.execute(r'UPDATE student_card'
                               r'   SET is_default = $1'
                               r' WHERE account_id = $2'
                               r'   AND is_default = $3',
                               False, account_id, True)

            (id_,) = await conn.fetchrow(r'INSERT INTO student_card'
                                         r'            (account_id, institute_id, student_id, email, is_default)'
                                         r'     VALUES ($1, $2, $3, $4, $5)'
                                         r'  RETURNING id',
                                         account_id, institute_id, student_id, email, True)

            return id_


async def read(student_card_id: int) -> do.StudentCard:
    async with SafeExecutor(
            event='get student card by id',
            sql=fr'SELECT id, institute_id, student_id, email, is_default'
                fr'  FROM student_card'
                fr' WHERE id = %(student_card)s',
            student_card=student_card_id,
            fetch=1,
    ) as (id_, institute_id, student_id, email, is_default):
        return do.StudentCard(id=id_, institute_id=institute_id, student_id=student_id,
                              email=email, is_default=is_default)


async def browse(account_id: int) -> Sequence[do.StudentCard]:

    async with SafeExecutor(
            event='browse student card by account id',
            sql=fr'SELECT id, institute_id, student_id, email, is_default'
                fr'  FROM student_card'
                fr' WHERE account_id = %(account_id)s',
            account_id=account_id,
            fetch='all',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.StudentCard(id=id_, institute_id=institute_id, student_id=student_id,
                               email=email, is_default=is_default)
                for (id_, institute_id, student_id, email, is_default) in records]


async def is_duplicate(institute_id: int, student_id: str) -> bool:
    async with SafeExecutor(
            event='check duplicate student card by institute_id and student_id',
            sql=fr'SELECT count(*)'
                fr'  FROM student_card'
                fr' WHERE institute_id = %(institute_id)s'
                fr'   AND student_id = %(student_id)s',
            institute_id=institute_id,
            student_id=student_id,
            fetch=1,
    ) as (cnt,):
        return cnt > 0


async def read_owner_id(student_card_id: int) -> int:
    async with SafeExecutor(
            event='get student owner id by student card id',
            sql=fr'SELECT account_id'
                fr'  FROM student_card'
                fr' WHERE id = %(student_card_id)s',
            student_card_id=student_card_id,
            fetch=1,
    ) as (id_,):
        return id_
