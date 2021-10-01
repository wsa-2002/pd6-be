from datetime import datetime

import persistence.database as db

from base import do, enum

add = db.peer_review_record.add
browse = db.peer_review_record.browse
read = db.peer_review_record.read
edit = db.peer_review_record.edit_score

add_auto = db.peer_review_record.add_auto
read_by_peer_review_id = db.peer_review_record.read_by_peer_review_id


async def get_review_submission(problem_id: int, account_id: int, selection_type: enum.TaskSelectionType,
                                challenge_end_time: datetime) -> do.Submission:
    judgment = await db.judgment.get_submission_judgment_by_challenge_type(problem_id=problem_id,
                                                                           account_id=account_id,
                                                                           selection_type=selection_type,
                                                                           challenge_end_time=challenge_end_time)
    return await db.submission.read(judgment.submission_id)
