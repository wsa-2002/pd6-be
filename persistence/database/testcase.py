from typing import Sequence, Optional
from uuid import UUID

from base import do

from .base import AutoTxConnection, OnlyExecute, FetchAll, FetchOne, ParamDict


async def add(problem_id: int, is_sample: bool, score: int, label: Optional[str], input_file_uuid: Optional[UUID],
              input_filename: Optional[str], output_file_uuid: Optional[UUID], output_filename: Optional[str],
              note: Optional[str], time_limit: int, memory_limit: int, is_disabled: bool) -> int:
    async with FetchOne(
            event='Add testcase',
            sql="INSERT INTO testcase"
                "            (problem_id, is_sample, score, label, input_file_uuid, output_file_uuid, input_filename,"
                "             output_filename, note, time_limit, memory_limit, is_disabled)"
                "     VALUES (%(problem_id)s, %(is_sample)s, %(score)s, %(label)s, %(input_file_uuid)s, "
                "             %(output_file_uuid)s, %(input_filename)s, %(output_filename)s, %(note)s,"
                "             %(time_limit)s, %(memory_limit)s, %(is_disabled)s)"
                "  RETURNING id",
            problem_id=problem_id, is_sample=is_sample, score=score, label=label, input_file_uuid=input_file_uuid,
            output_file_uuid=output_file_uuid, input_filename=input_filename, output_filename=output_filename,
            note=note, time_limit=time_limit, memory_limit=memory_limit, is_disabled=is_disabled,
    ) as (id_,):
        return id_


async def read(testcase_id: int, include_disabled=True, include_deleted=False) -> do.Testcase:
    async with FetchOne(
            event='read testcases with problem id',
            sql=fr'SELECT id, problem_id, is_sample, score, label, input_file_uuid, output_file_uuid, input_filename,'
                fr'       output_filename, note, time_limit, memory_limit, is_disabled, is_deleted'
                fr'  FROM testcase'
                fr' WHERE id = %(testcase_id)s'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            testcase_id=testcase_id,
    ) as (id_, problem_id, is_sample, score, label, input_file_uuid, output_file_uuid, input_filename, output_filename,
          note, time_limit, memory_limit, is_disabled, is_deleted):
        return do.Testcase(id=id_, problem_id=problem_id, is_sample=is_sample, score=score, label=label,
                           input_file_uuid=input_file_uuid, output_file_uuid=output_file_uuid,
                           input_filename=input_filename, output_filename=output_filename, note=note,
                           time_limit=time_limit, memory_limit=memory_limit,
                           is_disabled=is_disabled, is_deleted=is_deleted)


async def browse(problem_id: int, is_sample=None, include_disabled=False, include_deleted=False) \
        -> Sequence[do.Testcase]:
    async with FetchAll(
            event='browse testcases with problem id',
            sql=fr'SELECT id, problem_id, is_sample, score, label, input_file_uuid, output_file_uuid, input_filename,'
                fr'       output_filename, note, time_limit, memory_limit, is_disabled, is_deleted'
                fr'  FROM testcase'
                fr' WHERE problem_id = %(problem_id)s'
                fr'{" AND is_sample" if is_sample is True else ""}'
                fr'{" AND NOT is_sample" if is_sample is False else ""}'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY is_sample DESC, id ASC',
            problem_id=problem_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Testcase(id=id_, problem_id=problem_id, is_sample=is_sample, score=score, label=label,
                            input_file_uuid=input_file_uuid, output_file_uuid=output_file_uuid,
                            input_filename=input_filename, output_filename=output_filename, note=note,
                            time_limit=time_limit, memory_limit=memory_limit,
                            is_disabled=is_disabled, is_deleted=is_deleted)
                for (id_, problem_id, is_sample, score, label, input_file_uuid, output_file_uuid, input_filename,
                     output_filename, note, time_limit, memory_limit, is_disabled, is_deleted)
                in records]


async def edit(testcase_id: int,
               is_sample: bool = None,
               score: int = None,
               label: str = None,
               input_file_uuid: UUID = None,
               output_file_uuid: UUID = None,
               input_filename: str = None,
               output_filename: str = None,
               note: Optional[str] = ...,
               time_limit: int = None,
               memory_limit: int = None,
               is_disabled: bool = None, ) -> None:
    to_updates: ParamDict = {}

    if is_sample is not None:
        to_updates['is_sample'] = is_sample
    if score is not None:
        to_updates['score'] = score
    if label is not None:
        to_updates['label'] = label
    if input_file_uuid is not None:
        to_updates['input_file_uuid'] = input_file_uuid
    if output_file_uuid is not None:
        to_updates['output_file_uuid'] = output_file_uuid
    if input_filename is not None:
        to_updates['input_filename'] = input_filename
    if output_filename is not None:
        to_updates['output_filename'] = output_filename
    if note is not ...:
        to_updates['note'] = note
    if time_limit is not None:
        to_updates['time_limit'] = time_limit
    if memory_limit is not None:
        to_updates['memory_limit'] = memory_limit
    if is_disabled is not None:
        to_updates['is_disabled'] = is_disabled

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='edit testcase',
            sql=fr'UPDATE testcase'
                fr'   SET {set_sql}'
                fr' WHERE id = %(testcase_id)s',
            testcase_id=testcase_id,
            **to_updates,
    ):
        pass


async def disable_enable_testcase_by_problem(problem_id: int, testcase_disabled: bool, is_sample=False) -> None:
    async with OnlyExecute(
            event='disable or enable testcase by problem',
            sql=r'UPDATE testcase'
                r'   SET is_disabled = %(is_disabled)s'
                r' WHERE problem_id = %(problem_id)s'
                r'   AND is_sample = %(is_sample)s',
            is_disabled=testcase_disabled,
            problem_id=problem_id, is_sample=is_sample,
    ):
        pass


async def delete(testcase_id: int) -> None:
    async with OnlyExecute(
            event='soft delete testcase',
            sql=r'UPDATE testcase'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(testcase_id)s',
            testcase_id=testcase_id,
            is_deleted=True,
    ):
        pass


async def delete_input_data(testcase_id: int) -> None:
    async with OnlyExecute(
            event='delete testcase input data',
            sql=r'UPDATE testcase'
                r'   SET input_file_uuid = NULL'
                r' WHERE id = %(testcase_id)s',
            testcase_id=testcase_id,
    ):
        pass


async def delete_output_data(testcase_id: int) -> None:
    async with OnlyExecute(
            event='delete testcase output data',
            sql=r'UPDATE testcase'
                r'   SET output_file_uuid = NULL'
                r' WHERE id = %(testcase_id)s',
            testcase_id=testcase_id,
    ):
        pass


async def delete_cascade_from_problem(problem_id: int, cascading_conn=None) -> None:
    if cascading_conn:
        await _delete_cascade_from_problem(problem_id, conn=cascading_conn)
        return

    async with AutoTxConnection(event=f'cascade delete testcase from problem {problem_id=}') as conn:
        await _delete_cascade_from_problem(problem_id, conn=conn)


async def _delete_cascade_from_problem(problem_id: int, conn) -> None:
    await conn.execute(r'UPDATE testcase'
                       r'   SET is_deleted = $1'
                       r' WHERE problem_id = $2',
                       True, problem_id)
