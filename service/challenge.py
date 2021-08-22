from typing import Tuple, Sequence

from base import do
import persistence.database as db


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


async def browse_task_status(challenge_id: int, account_id: int) \
        -> Sequence[Tuple[do.Problem, do.Submission]]:
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)

    return [await db.problem.read_task_status_by_type(
                problem_id=problem.id,
                selection_type=challenge.selection_type,
                challenge_end_time=challenge.end_time,
                account_id=account_id)
            for problem in problems]
