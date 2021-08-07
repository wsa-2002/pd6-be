import persistence.database as db


add = db.problem.add
browse = db.problem.browse
read = db.problem.read
edit = db.problem.edit
delete = db.problem.delete_cascade

browse_problem_set = db.problem.browse_problem_set
