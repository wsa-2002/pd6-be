from typing import Sequence, Optional, Tuple

from base import do, enum

from . import scoreboard
from .base import SafeExecutor, SafeConnection


async def add_under_scoreboard(challenge_id: int, challenge_label: str, title: str, target_problem_ids: Sequence[int],
                               type: enum.ScoreboardType, scoring_formula: str, baseline_team_id: Optional[int],
                               rank_by_total_score: bool, team_label_filter: Optional[str]) -> int:
    async with SafeConnection(event=f'add scoreboard_setting_team_project under scoreboard') as conn:
        async with conn.transaction():
            (team_project_scoreboard_id,) = await conn.fetchrow(
                "INSERT INTO scoreboard_setting_team_project"
                "            (scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter)"
                "     VALUES ($1, $2, $3, $4)"
                "  RETURNING id",
                scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter,
            )

            (scoreboard_id,) = await conn.fetchrow(
                "INSERT INTO scoreboard"
                "            (challenge_id, challenge_label, title, target_problem_ids, type, setting_id)"
                "     VALUES ($1, $2, $3, $4, $5, $6) "
                "  RETURNING id",
                challenge_id, challenge_label, title, target_problem_ids, type, team_project_scoreboard_id,
            )

            return scoreboard_id


async def read(scoreboard_setting_team_project_id: int, include_deleted=False) -> do.ScoreboardSettingTeamProject:
    async with SafeExecutor(
            event='read scoreboard_setting_team_project',
            sql=fr'SELECT id, scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter'
                fr'  FROM scoreboard_setting_team_project'
                fr' WHERE id = %(scoreboard_setting_team_project_id)s',
            scoreboard_setting_team_project_id=scoreboard_setting_team_project_id,
            fetch=1,
    ) as (id_, scoring_formula, baseline_team_id, rank_by_total_score, team_label_filter):
        return do.ScoreboardSettingTeamProject(id=id_, scoring_formula=scoring_formula, baseline_team_id=baseline_team_id,
                                               rank_by_total_score=rank_by_total_score, team_label_filter=team_label_filter)


async def edit_with_scoreboard(scoreboard_id: int,
                               challenge_label: str = None,
                               title: str = None,
                               target_problem_ids: Sequence[int] = None,
                               scoring_formula: str = None,
                               baseline_team_id: Optional[int] = ...,
                               rank_by_total_score: bool = None,
                               team_label_filter: Optional[str] = ...) -> None:
    scoreboard_to_updates = {}

    if challenge_label is not None:
        scoreboard_to_updates['challenge_label'] = challenge_label
    if title is not None:
        scoreboard_to_updates['title'] = title
    if target_problem_ids is not None:
        scoreboard_to_updates['target_problem_ids'] = target_problem_ids

    scoreboard_setting_to_updates = {}

    if scoring_formula is not None:
        scoreboard_setting_to_updates['scoring_formula'] = scoring_formula
    if baseline_team_id is not ...:
        scoreboard_setting_to_updates['baseline_team_id'] = baseline_team_id
    if rank_by_total_score is not None:
        scoreboard_setting_to_updates['rank_by_total_score'] = rank_by_total_score
    if team_label_filter is not ...:
        scoreboard_setting_to_updates['team_label_filter'] = team_label_filter

    if scoreboard_to_updates:
        set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in scoreboard_to_updates)

        async with SafeExecutor(
                event='edit scoreboard',
                sql=fr'UPDATE scoreboard'
                    fr'   SET {set_sql}'
                    fr' WHERE id = %(scoreboard_id)s',
                scoreboard_id=scoreboard_id,
                **scoreboard_to_updates,
        ):
            pass

    if scoreboard_setting_to_updates:
        scoreboard_ = await scoreboard.read(scoreboard_id=scoreboard_id)
        set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in scoreboard_setting_to_updates)

        async with SafeExecutor(
                event='edit scoreboard_setting_team_project',
                sql=fr'UPDATE scoreboard_setting_team_project'
                    fr'   SET {set_sql}'
                    fr' WHERE id = %(scoreboard_setting_team_project_id)s',
                scoreboard_setting_team_project_id=scoreboard_.setting_id,
                **scoreboard_setting_to_updates,
        ):
            pass


async def get_problem_raw_score(problem_id: int, team_member_ids: Sequence[int]) \
    -> Tuple[do.Problem, do.Submission, do.Judgment]:

    """
    Return: latest problem submission of all team members (latest judgment)
    """

    member_ids_sql = '(' + ', '.join(str(team_member_id) for team_member_id in team_member_ids) + ')'
    async with SafeExecutor(
            event='get problem normal score',
            sql=fr'SELECT problem.id, problem.challenge_id, problem.challenge_label, problem.title, problem.setter_id,' 
		        fr'       problem.full_score, problem.description, problem.io_description, problem.source, problem.hint, problem.is_deleted,'
                fr'       submission.id, submission.account_id, submission.problem_id, submission.language_id,'
		        fr'       submission.filename, submission.content_file_uuid, submission.content_length, submission.submit_time,'
                fr'       judgment.id, judgment.submission_id, judgment.verdict, judgment.total_time,'
		        fr'       judgment.max_memory, judgment.score, judgment.judge_time'
                fr'  FROM submission'
                fr' INNER JOIN problem'
                fr'         ON problem.id = submission.problem_id'
                fr'        AND NOT problem.is_deleted'
                fr' INNER JOIN challenge'
                fr'         ON challenge.id = problem.challenge_id'
                fr' INNER JOIN judgment'
                fr'         ON judgment.submission_id = submission.id'
                fr'        AND judgment.id = submission_last_judgment_id(submission.id)'    
                fr' WHERE account_id IN {member_ids_sql}'
                fr'   AND problem.id = %(problem_id)s'
                fr'   AND submission.submit_time <= challenge.end_time'
                fr' ORDER BY submission.submit_time DESC, submission.id DESC',
            problem_id=problem_id,
            fetch=1,
    ) as (problem_id, challenge_id, challenge_label, title, setter_id, full_score,
          description, io_description, source, hint, is_deleted,
          submission_id, account_id, problem_id, language_id, filename, content_file_uuid, content_length, submit_time,
          judgment_id, submission_id, verdict, total_time, max_memory, score, judge_time):
        return (do.Problem(id=problem_id,
                           challenge_id=challenge_id, challenge_label=challenge_label,
                           title=title, setter_id=setter_id, full_score=full_score,
                           description=description, io_description=io_description, source=source, hint=hint,
                           is_deleted=is_deleted),
                do.Submission(id=submission_id, account_id=account_id, problem_id=problem_id, language_id=language_id,
                              filename=filename, content_file_uuid=content_file_uuid,
                              content_length=content_length, submit_time=submit_time),
                do.Judgment(id=judgment_id, submission_id=submission_id, verdict=enum.VerdictType(verdict),
                            total_time=total_time, max_memory=max_memory, score=score, judge_time=judge_time))
