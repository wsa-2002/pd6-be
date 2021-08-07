from typing import Tuple, Sequence

from base import do
import persistence.database as db


add = db.challenge.add
browse = db.challenge.browse
read = db.challenge.read
edit = db.challenge.edit
delete = db.challenge.delete


async def browse_task(challenge_id: int) -> Tuple[
    Sequence[do.Problem],
    Sequence[do.PeerReview],
]:
    return (
        await db.problem.browse_by_challenge(challenge_id=challenge_id),
        await db.peer_review.browse_by_challenge(challenge_id=challenge_id),
    )
