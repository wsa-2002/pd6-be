from typing import Tuple, Sequence

from base import do
import persistence.database as db
import exceptions as exc

add = db.challenge.add
browse = db.challenge.browse
read = db.challenge.read
edit = db.challenge.edit
delete = db.challenge.delete_cascade


async def browse_task(challenge_id: int) -> Tuple[
    Sequence[do.Problem],
    Sequence[do.PeerReview],
    Sequence[do.Essay]
]:
    return (
        await db.problem.browse_by_challenge(challenge_id=challenge_id),
        await db.peer_review.browse_by_challenge(challenge_id=challenge_id),
        await db.essay.browse_by_challenge(challenge_id=challenge_id),
    )


async def browse_task_status(challenge_id: int, account_id: int = None) \
        -> Sequence[Tuple[do.Problem, do.Submission]]:
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)

    return [await db.problem.read_task_status_by_type(
        problem_id=problem.id,
        selection_type=challenge.selection_type,
        account_id=account_id)
            for problem in problems]


async def get_challenge_statistics(challenge_id: int) -> Sequence[Tuple[str, int, int, int]]:
    problems = await db.problem.browse_by_challenge(challenge_id)
    return [(problem.challenge_label,
             await db.problem.total_ac_member_count(problem.id),
             await db.problem.total_submission_count(problem.id),
             await db.problem.total_member_count(problem.id))
            for problem in problems]


async def get_member_submission_statistics(challenge_id: int) \
        -> Sequence[Tuple[int, Sequence[do.Judgment], Sequence[do.EssaySubmission]]]:
    """
    :return: [id, [submission_id, submission_score], [essay_submission]]
    """

    challenge = await db.challenge.read(challenge_id, include_scheduled=True)
    class_members = await db.class_.browse_members(class_id=challenge.class_id)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)
    essays = await db.essay.browse_by_challenge(challenge_id=challenge_id)
    result = []
    for class_member in class_members:
        problem_scores = []
        for problem in problems:
            try:
                problem_scores.append(await db.judgment.get_submission_score(problem_id=problem.id,
                                                                             account_id=class_member.member_id,
                                                                             selection_type=challenge.selection_type,
                                                                             challenge_end_time=challenge.end_time))
            except exc.persistence.NotFound:
                pass

        essay_submissions = []
        for essay in essays:
            try:
                essay_submissions.append(
                    await db.essay_submission.get_latest_essay_submission(account_id=class_member.member_id,
                                                                          essay_id=essay.id))
            except exc.persistence.NotFound:
                pass
        result.append((class_member.member_id, problem_scores, essay_submissions))
    return result
