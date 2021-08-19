import persistence.database as db


browse = db.peer_review_record.browse
read = db.peer_review_record.read
edit = db.peer_review_record.edit_score


async def add():
    return
