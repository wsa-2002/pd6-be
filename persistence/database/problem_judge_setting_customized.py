from uuid import UUID

from base import do

from .base import FetchOne


async def add(judge_code_file_uuid: UUID, judge_code_filename: str) -> int:
    async with FetchOne(
            event='add problem judge setting customized',
            sql=fr'INSERT INTO problem_judge_setting_customized'
                fr'            (judge_code_file_uuid, judge_code_filename)'
                fr'     VALUES (%(judge_code_file_uuid)s, %(judge_code_filename)s)'
                fr'  RETURNING id',
            judge_code_file_uuid=judge_code_file_uuid, judge_code_filename=judge_code_filename,
    ) as (customized_id,):
        return customized_id


async def read(customized_id: int) -> do.ProblemJudgeSettingCustomized:
    async with FetchOne(
            event='read customized judge setting',
            sql=fr'SELECT id, judge_code_file_uuid, judge_code_filename'
                fr'  FROM problem_judge_setting_customized'
                fr' WHERE id = %(customized_id)s',
            customized_id=customized_id,
    ) as (id_, judge_code_file_uuid, judge_code_filename):
        return do.ProblemJudgeSettingCustomized(id=id_, judge_code_file_uuid=judge_code_file_uuid,
                                                judge_code_filename=judge_code_filename)
