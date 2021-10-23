from typing import Optional
import io

from base import do
from base.enum import ProblemJudgeType
import const
import persistence.database as db
import persistence.s3 as s3


add = db.problem.add
browse = db.problem.browse
read = db.problem.read
delete = db.problem.delete_cascade

browse_problem_set = db.problem.browse_problem_set
read_task_status_by_type = db.problem.read_task_status_by_type


async def edit(problem_id: int,
               judge_type: ProblemJudgeType,
               challenge_label: str = None,
               title: str = None,
               full_score: int = None,
               testcase_disabled: bool = None,
               judge_code: Optional[str] = None,
               description: Optional[str] = ...,
               io_description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,) -> None:
    # write code into file
    setting_id = None
    if judge_code:
        with io.BytesIO(judge_code.encode(const.JUDGE_CODE_ENCODING)) as file:
            s3_file = await s3.customized_code.upload(file=file)

        s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

        setting_id = await db.problem_judge_setting_customized.add(judge_code_uuid=s3_file_uuid, filename=str(s3_file_uuid))

    await db.problem.edit(problem_id, challenge_label=challenge_label, title=title, full_score=full_score,
                          description=description, io_description=io_description, source=source, hint=hint,
                          setting_id=setting_id if judge_code else None, judge_type=judge_type)

    if testcase_disabled is not None:
        await db.testcase.disable_enable_testcase_by_problem(problem_id=problem_id,
                                                             testcase_disabled=testcase_disabled)
