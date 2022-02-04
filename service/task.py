from typing import Sequence

from base import do
from persistence import database as db


async def browse(challenge_id: int) -> tuple[
    Sequence[do.Problem],
    Sequence[do.PeerReview],
    Sequence[do.Essay],
    Sequence[do.Scoreboard]
]:
    return (
        await db.problem.browse_by_challenge(challenge_id=challenge_id),
        await db.peer_review.browse_by_challenge(challenge_id=challenge_id),
        await db.essay.browse_by_challenge(challenge_id=challenge_id),
        await db.scoreboard.browse_by_challenge(challenge_id=challenge_id),
    )


async def browse_status(challenge_id: int, account_id: int) \
        -> Sequence[tuple[do.Problem, do.Submission]]:
    challenge = await db.challenge.read(challenge_id=challenge_id)
    problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)

    return [
        await db.problem.read_task_status_by_type(
            problem_id=problem.id,
            selection_type=challenge.selection_type,
            challenge_end_time=challenge.end_time,
            account_id=account_id,
        )
        for problem in problems
    ]
