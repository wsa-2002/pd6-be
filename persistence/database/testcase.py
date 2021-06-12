from typing import Sequence

import log
from base import do

from .base import SafeExecutor


@log.timed
async def add(problem_id: int, is_sample: bool, score: int, input_file: str, output_file: str,
              time_limit: int, memory_limit: int, is_disabled: bool) -> int:
    async with SafeExecutor(
            event='Add testcase',
            sql="INSERT INTO testcase"
                "            (problem_id, is_sample, score, input_file, output_file,"
                "             time_limit, memory_limit, is_disabled)"
                "     VALUES (%(problem_id)s, %(is_sample)s, %(score)s, %(input_file)s, %(output_file)s,"
                "             %(time_limit)s, %(memory_limit)s, %(is_disabled)s)"
                "  RETURNING id",
            problem_id=problem_id, is_sample=is_sample, score=score, input_file=input_file, output_file=output_file,
            time_limit=time_limit, memory_limit=memory_limit, is_disabled=is_disabled,
            fetch=1,
    ) as (id_,):
        return id_


@log.timed
async def read(testcase_id: int, include_disabled=False, include_deleted=False) -> do.Testcase:
    async with SafeExecutor(
            event='read testcases with problem id',
            sql=fr'SELECT problem_id, is_sample, score, input_file, output_file, '
                fr'       time_limit, memory_limit, is_disabled, is_deleted'
                fr'  FROM testcase'
                fr' WHERE id = %(testcase_id)s'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            testcase_id=testcase_id,
            fetch=1,
    ) as (problem_id, is_sample, score, input_file, output_file,
          time_limit, memory_limit, is_disabled, is_deleted):
        return do.Testcase(id=testcase_id, problem_id=problem_id, is_sample=is_sample, score=score,
                           input_file=input_file, output_file=output_file,
                           time_limit=time_limit, memory_limit=memory_limit,
                           is_disabled=is_disabled, is_deleted=is_deleted)


@log.timed
async def browse(problem_id: int, include_disabled=False, include_deleted=False) -> Sequence[do.Testcase]:
    async with SafeExecutor(
            event='browse testcases with problem id',
            sql=fr'SELECT id, is_sample, score, input_file, output_file, '
                fr'       time_limit, memory_limit, is_disabled, is_deleted'
                fr'  FROM testcase'
                fr' WHERE problem_id = %(problem_id)s'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY is_sample DESC, id ASC',
            problem_id=problem_id,
            fetch='all',
    ) as records:
        return [do.Testcase(id=id_, problem_id=problem_id, is_sample=is_sample, score=score,
                            input_file=input_file, output_file=output_file,
                            time_limit=time_limit, memory_limit=memory_limit,
                            is_disabled=is_disabled, is_deleted=is_deleted)
                for (id_, problem_id, is_sample, score, input_file, output_file,
                     time_limit, memory_limit, is_disabled, is_deleted)
                in records]


@log.timed
async def edit(testcase_id: int,
               is_sample: bool = None,
               score: int = None,
               input_file: str = None,
               output_file: str = None,
               time_limit: int = None,
               memory_limit: int = None,
               is_disabled: bool = None,) -> None:
    to_updates = {}

    if is_sample is not None:
        to_updates['is_sample'] = is_sample
    if score is not None:
        to_updates['score'] = score
    if input_file is not None:
        to_updates['input_file'] = input_file
    if output_file is not None:
        to_updates['output_file'] = output_file
    if time_limit is not None:
        to_updates['time_limit'] = time_limit
    if memory_limit is not None:
        to_updates['memory_limit'] = memory_limit
    if is_disabled is not None:
        to_updates['is_disabled'] = is_disabled

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit testcase',
            sql=fr'UPDATE testcase'
                fr'   SET {set_sql}'
                fr' WHERE id = %(testcase_id)s',
            testcase_id=testcase_id,
            **to_updates,
    ):
        pass


@log.timed
async def delete(testcase_id: int) -> None:
    async with SafeExecutor(
            event='soft delete testcase',
            sql=fr'UPDATE testcase'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(testcase_id)s',
            testcase_id=testcase_id,
            is_deleted=True,
    ):
        pass
