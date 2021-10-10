from typing import Optional, Tuple

import persistence.database as db


add = db.problem.add
browse = db.problem.browse
read = db.problem.read
delete = db.problem.delete_cascade

browse_problem_set = db.problem.browse_problem_set
read_task_status_by_type = db.problem.read_task_status_by_type


async def edit(problem_id: int,
               challenge_label: str = None,
               title: str = None,
               full_score: int = None,
               testcase_disabled: bool = None,
               description: Optional[str] = ...,
               io_description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,) -> None:

    await db.problem.edit(problem_id, challenge_label=challenge_label, title=title, full_score=full_score, description=description,
                          io_description=io_description, source=source, hint=hint)
    if testcase_disabled is not None:
        await db.testcase.disable_enable_testcase_by_problem(problem_id=problem_id,
                                                             testcase_disabled=testcase_disabled)


async def get_problem_statistics(problem_id: int) -> Tuple[int, int, int]:
    return (await db.problem.total_ac_member_count(problem_id),
            await db.problem.total_submission_count(problem_id),
            await db.problem.total_member_count(problem_id))
