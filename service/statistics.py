from typing import Tuple, Sequence

from base import do
from base.enum import RoleType
from persistence import database as db


async def get_challenge_statistics(challenge_id: int) -> Sequence[Tuple[str, int, int, int]]:
    problems = await db.problem.browse_by_challenge(challenge_id)
    return [(problem.challenge_label,
             await db.problem.class_total_ac_member_count(problem_id=problem.id),
             await db.problem.class_total_submission_count(problem_id=problem.id, challenge_id=challenge_id),
             await db.problem.class_total_member_count(problem_id=problem.id))
            for problem in problems]


async def get_member_submission_statistics(challenge_id: int) \
        -> Sequence[Tuple[int, Sequence[tuple[int, do.Judgment]], Sequence[do.EssaySubmission]]]:
    """
    :return: [id, [problem_id, judgment], [essay_submission]]
    """

    challenge = await db.challenge.read(challenge_id)
    class_members = await db.class_.browse_members(class_id=challenge.class_id)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)
    essays = await db.essay.browse_by_challenge(challenge_id=challenge_id)

    problem_to_member_judgments = {
        problem.id: await db.judgment.browse_by_problem_class_members(problem_id=problem.id,
                                                                      selection_type=challenge.selection_type)
        for problem in problems
    }

    essay_to_member_essay_submissions = {
        essay.id: await db.essay_submission.browse_by_essay_class_members(essay_id=essay.id)
        for essay in essays
    }

    result = []
    for class_member in class_members:
        if class_member.role != RoleType.normal:
            continue

        problem_judgments = []
        for problem in problems:
            try:
                judgment = problem_to_member_judgments[problem.id][class_member.member_id]
            except KeyError:
                pass
            else:
                problem_judgments.append((problem.id, judgment))

        essay_submissions = []
        for essay in essays:
            try:
                essay_submission = essay_to_member_essay_submissions[essay.id][class_member.member_id]
            except KeyError:
                pass
            else:
                essay_submissions.append(essay_submission)

        result.append((class_member.member_id, problem_judgments, essay_submissions))

    return result


async def get_problem_statistics(problem_id: int) -> Tuple[int, int, int]:
    return (await db.problem.total_ac_member_count(problem_id),
            await db.problem.total_submission_count(problem_id),
            await db.problem.total_member_count(problem_id))
