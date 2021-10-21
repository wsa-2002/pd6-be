import persistence.database as db


add_under_scoreboard = db.scoreboard_setting_team_project.add_under_scoreboard
edit_with_scoreboard = db.scoreboard_setting_team_project.edit_with_scoreboard


async def calculate_score(formula: str, team_score: int, class_best: int, class_worst: int, baseline:int) -> int:
    return eval(formula)
