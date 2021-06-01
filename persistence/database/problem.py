from typing import Optional, Sequence

from base import do, enum

from .base import SafeExecutor


async def add(type_: enum.ProblemType, name: str, setter_id: int, full_score: int,
              description: Optional[str], source: Optional[str], hint: Optional[str],
              is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='Add problem',
            sql="INSERT INTO problem"
                "            (type, name, setter_id, full_score,"
                "             description, source, hint, is_enabled, is_hidden)"
                "     VALUES (%(type)s, %(name)s, %(setter_id)s, %(full_score)s,"
                "             %(description)s, %(source)s, %(hint)s, %(is_enabled)s, %(is_hidden)s)"
                "  RETURNING id",
            type=type_, name=name, setter_id=setter_id, full_score=full_score,
            description=description, source=source, hint=hint, is_enabled=is_enabled, is_hidden=is_hidden,
            fetch=1,
    ) as (id_,):
        return id_


async def browse() -> Sequence[do.Problem]:
    async with SafeExecutor(
            event='browse problems',
            sql='SELECT id, type, name, setter_id, full_score, description, source, hint, is_enabled, is_hidden'
                '  FROM problem'
                ' ORDER BY id ASC',
            fetch='all',
    ) as results:
        return [do.Problem(id=id_, type=type_, name=name, setter_id=setter_id,
                           full_score=full_score, description=description, source=source, hint=hint,
                           is_enabled=is_enabled, is_hidden=is_hidden)
                for id_, type_, name, setter_id, full_score, description, source, hint, is_enabled, is_hidden
                in results]


async def read(problem_id: int) -> do.Problem:
    async with SafeExecutor(
            event='read problem by id',
            sql='SELECT id, type, name, setter_id, full_score, description, source, hint, is_enabled, is_hidden'
                '  FROM problem'
                ' WHERE id = %(problem_id)s',
            problem_id=problem_id,
            fetch='all',
    ) as (id_, type_, name, setter_id, full_score, description, source, hint, is_enabled, is_hidden):
        return do.Problem(id=id_, type=type_, name=name, setter_id=setter_id,
                          full_score=full_score, description=description, source=source, hint=hint,
                          is_enabled=is_enabled, is_hidden=is_hidden)


async def edit(problem_id: int,
               type_: Optional[enum.ChallengeType] = None,
               name: Optional[str] = None,
               full_score: Optional[int] = None,
               description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,
               is_enabled: Optional[bool] = None,
               is_hidden: Optional[bool] = None) -> None:
    to_updates = {}

    if type_ is not None:
        to_updates['type'] = type_
    if name is not None:
        to_updates['name'] = name
    if full_score is not None:
        to_updates['full_score'] = full_score
    if description is not ...:
        to_updates['description'] = description
    if source is not ...:
        to_updates['source'] = source
    if hint is not ...:
        to_updates['hint'] = hint
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled
    if is_hidden is not None:
        to_updates['is_hidden'] = is_hidden

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    if set_sql:
        async with SafeExecutor(
                event='edit problem',
                sql=fr'UPDATE problem'
                    fr' WHERE id = %(problem_id)s'
                    fr'   SET {set_sql}',
                problem_id=problem_id,
                **to_updates,
        ):
            pass


async def delete(problem_id: int) -> None:
    ...  # TODO


async def add_testcase(problem_id: int, is_sample: bool, score: int, input_file: str, output_file: str,
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


async def browse_testcases(problem_id: int) -> Sequence[do.Testcase]:
    async with SafeExecutor(
            event='browse testcases with problem id',
            sql='SELECT id, is_sample, score, input_file, output_file, '
                '       time_limit, memory_limit, is_enabled, is_hidden'
                '  FROM testcase'
                ' WHERE problem_id = %(problem_id)s'
                ' ORDER BY is_sample DESC, id ASC',
            problem_id=problem_id,
            fetch='all',
    ) as results:
        return [do.Testcase(id=id_, problem_id=problem_id, is_sample=is_sample, score=score,
                            input_file=input_file, output_file=output_file,
                            time_limit=time_limit, memory_limit=memory_limit,
                            is_enabled=is_enabled, is_hidden=is_hidden)
                for (id_, problem_id, is_sample, score, input_file, output_file,
                     time_limit, memory_limit, is_enabled, is_hidden)
                in results]
