import persistence.database as db

add = db.peer_review_record.add
browse = db.peer_review_record.browse
read = db.peer_review_record.read
edit = db.peer_review_record.edit_score

add_auto = db.peer_review_record.add_auto