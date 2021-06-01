from typing import Optional, Sequence

from base import do

from .base import SafeExecutor


async def read(testdata_id: int) -> do.Testdata:
    async with SafeExecutor(
            event='browse testdatas with problem id',
            sql='SELECT problem_id, is_sample, score, input_file, output_file, '
                '       time_limit, memory_limit, is_enabled, is_hidden'
                '  FROM testdata'
                ' WHERE id = %(testdata_id)s',
            testdata_id=testdata_id,
            fetch='all',
    ) as (problem_id, is_sample, score, input_file, output_file,
          time_limit, memory_limit, is_enabled, is_hidden):
        return do.Testdata(id=testdata_id, problem_id=problem_id, is_sample=is_sample, score=score,
                           input_file=input_file, output_file=output_file,
                           time_limit=time_limit, memory_limit=memory_limit,
                           is_enabled=is_enabled, is_hidden=is_hidden)


async def edit(testdata_id: int,
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

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    if set_sql:
        async with SafeExecutor(
                event='edit testdata',
                sql=fr'UPDATE testdata'
                    fr' WHERE id = %(testdata_id)s'
                    fr'   SET {set_sql}',
                testdata_id=testdata_id,
                **to_updates,
        ):
            pass


async def delete(testdata_id: int) -> None:
    ...  # TODO
