from typing import Optional, Sequence

from base import do

from .base import SafeExecutor


async def add(problem_id: int, is_sample: bool, score: int, input_file: str, output_file: str,
              time_limit: int, memory_limit: int, is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='Add testcase',
            sql="INSERT INTO testcase"
                "            (problem_id, is_sample, score, input_file, output_file,"
                "             time_limit, memory_limit, is_enabled, is_hidden)"
                "     VALUES (%(problem_id)s, %(is_sample)s, %(score)s, %(input_file)s, %(output_file)s,"
                "             %(time_limit)s, %(memory_limit)s, %(is_enabled)s, %(is_hidden)s)"
                "  RETURNING id",
            problem_id=problem_id, is_sample=is_sample, score=score, input_file=input_file, output_file=output_file,
            time_limit=time_limit, memory_limit=memory_limit, is_enabled=is_enabled, is_hidden=is_hidden,
            fetch=1,
    ) as (id_,):
        return id_


async def read(testcase_id: int) -> do.Testcase:
    async with SafeExecutor(
            event='read testcases with problem id',
            sql='SELECT problem_id, is_sample, score, input_file, output_file, '
                '       time_limit, memory_limit, is_enabled, is_hidden'
                '  FROM testcase'
                ' WHERE id = %(testcase_id)s',
            testcase_id=testcase_id,
            fetch=1,
    ) as (problem_id, is_sample, score, input_file, output_file,
          time_limit, memory_limit, is_enabled, is_hidden):
        return do.Testcase(id=testcase_id, problem_id=problem_id, is_sample=is_sample, score=score,
                           input_file=input_file, output_file=output_file,
                           time_limit=time_limit, memory_limit=memory_limit,
                           is_enabled=is_enabled, is_hidden=is_hidden)


async def browse(problem_id: int) -> Sequence[do.Testcase]:
    async with SafeExecutor(
            event='browse testcases with problem id',
            sql='SELECT id, is_sample, score, input_file, output_file, '
                '       time_limit, memory_limit, is_enabled, is_hidden'
                '  FROM testcase'
                ' WHERE problem_id = %(problem_id)s'
                ' ORDER BY is_sample DESC, id ASC',
            problem_id=problem_id,
            fetch='all',
    ) as records:
        return [do.Testcase(id=id_, problem_id=problem_id, is_sample=is_sample, score=score,
                            input_file=input_file, output_file=output_file,
                            time_limit=time_limit, memory_limit=memory_limit,
                            is_enabled=is_enabled, is_hidden=is_hidden)
                for (id_, problem_id, is_sample, score, input_file, output_file,
                     time_limit, memory_limit, is_enabled, is_hidden)
                in records]


async def edit(testcase_id: int,
               is_sample: Optional[bool] = None,
               score: Optional[int] = None,
               input_file: Optional[str] = None,
               output_file: Optional[str] = None,
               time_limit: Optional[int] = None,
               memory_limit: Optional[int] = None,
               is_enabled: Optional[bool] = None,
               is_hidden: Optional[bool] = None) -> None:
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
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit testcase',
            sql=fr'UPDATE testcase'
                fr' WHERE id = %(testcase_id)s'
                fr'   SET {set_sql}',
            testcase_id=testcase_id,
            **to_updates,
    ):
        pass


async def delete(testcase_id: int) -> None:
    ...  # TODO
