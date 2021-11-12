from datetime import datetime

import persistence.database as db

from base import do, enum

add = db.peer_review_record.add
browse = db.peer_review_record.browse
read = db.peer_review_record.read
edit = db.peer_review_record.edit_score

read_by_peer_review_id = db.peer_review_record.read_by_peer_review_id


async def add_auto(peer_review_id: int, grader_id: int) -> list[int]:
    peer_review = await db.peer_review.read(peer_review_id)
    peer_review_record_ids = []
    for time in range(peer_review.max_review_count):
        peer_review_record_ids += [await db.peer_review_record.add_auto(peer_review_id=peer_review_id,
                                                                        grader_id=grader_id)]

    return peer_review_record_ids
