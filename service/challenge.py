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


async def browse_task_status(challenge_id: int, account_id: int = None) \
        -> Sequence[Tuple[do.Problem, do.Submission]]:
    return await db.submission.browse_by_challenge(challenge_id=challenge_id, account_id=account_id)
