from typing import Optional

import persistence.database as db


add = db.problem.add
browse = db.problem.browse
read = db.problem.read
delete = db.problem.delete_cascade

browse_problem_set = db.problem.browse_problem_set


async def edit(problem_id: int,
               title: str = None,
               full_score: int = None,
               testcase_disabled: bool = None,
               description: Optional[str] = ...,
               source: Optional[str] = ...,
               hint: Optional[str] = ...,) -> None:

    await db.problem.edit(problem_id, title=title, full_score=full_score,
                          description=description, source=source, hint=hint)
    if testcase_disabled is not None:
        await db.testcase.disable_enable_testcase_by_problem(problem_id=problem_id,
                                                             testcase_disabled=testcase_disabled)
