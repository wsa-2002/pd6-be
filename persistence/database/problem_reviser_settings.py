from uuid import UUID

from base import do

from .base import FetchOne


async def add_customized(judge_code_file_uuid: UUID, judge_code_filename: str) -> int:
    async with FetchOne(
            event='add problem reviser setting customized',
            sql=r'INSERT INTO problem_reviser_setting_customized'
                r'            (judge_code_file_uuid, judge_code_filename)'
                r'     VALUES (%(judge_code_file_uuid)s, %(judge_code_filename)s)'
                r'  RETURNING id',
            judge_code_file_uuid=judge_code_file_uuid, judge_code_filename=judge_code_filename,
    ) as (customized_id,):
        return customized_id


async def read_customized(customized_id: int) -> do.ProblemJudgeSettingCustomized:
    async with FetchOne(
            event='read customized reviser setting',
            sql=r'SELECT id, judge_code_file_uuid, judge_code_filename'
                r'  FROM problem_reviser_setting_customized'
                r' WHERE id = %(customized_id)s',
            customized_id=customized_id,
    ) as (id_, judge_code_file_uuid, judge_code_filename):
        return do.ProblemJudgeSettingCustomized(id=id_, judge_code_file_uuid=judge_code_file_uuid,
                                                judge_code_filename=judge_code_filename)
