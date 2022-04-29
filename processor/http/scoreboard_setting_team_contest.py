import datetime
import math
from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel, constr

from base.enum import RoleType, ScoreboardType, VerdictType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from util import model
from util.context import context

router = APIRouter(
    tags=['Team Contest Scoreboard'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class ViewTeamContestScoreboardProblemScoreOutput:
    problem_id: int
    submit_count: int
    is_solved: bool
    solve_time: int  # in minutes
    is_first: bool
    penalty: float
    submission_id: int


@dataclass
class ViewTeamContestScoreboardOutput:
    team_id: int
    team_name: str
    total_penalty: Optional[float]
    solved_problem_count: int
    target_problem_data: Sequence[ViewTeamContestScoreboardProblemScoreOutput]


@router.get('/team-contest-scoreboard/view/{scoreboard_id}')
@enveloped
async def view_team_contest_scoreboard(scoreboard_id: int) \
        -> Sequence[ViewTeamContestScoreboardOutput]:
    """
    ### 權限
    - System Normal
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.normal, scoreboard_id=scoreboard_id):
        raise exc.NoPermission

    scoreboard = await db.scoreboard.read(scoreboard_id)
    if scoreboard.type != ScoreboardType.team_contest:
        raise exc.IllegalInput

    setting_data = await db.scoreboard_setting_team_contest.read(scoreboard.setting_id)

    class_id = (await db.challenge.read(challenge_id=scoreboard.challenge_id)).class_id
    teams = await db.team.browse_with_team_label_filter(class_id=class_id,
                                                        team_label_filter=setting_data.team_label_filter)
    challenge = await db.challenge.read(scoreboard.challenge_id)

    team_problem_datas: dict[int, list[ViewTeamContestScoreboardProblemScoreOutput]] = {team.id: [] for team in teams}

    for problem_id in scoreboard.target_problem_ids:

        team_verdict_infos = await db.judgment.get_class_all_team_all_submission_verdict(
            problem_id=problem_id, class_id=class_id, team_ids=[team.id for team in teams])

        first_solve_team_id = None
        team_solve_mins: dict[int, int] = {}
        team_wa_count: dict[int, int] = {}
        team_submit_count: dict[int, int] = {}
        team_submission_id: dict[int, int] = {}

        for team_id, submission_id, submit_time, verdict in team_verdict_infos:
            if team_id in team_solve_mins:
                continue
            team_submit_count[team_id] = team_submit_count.get(team_id, 0) + 1
            team_submission_id[team_id] = submission_id

            if verdict is VerdictType.accepted:
                if not first_solve_team_id:
                    first_solve_team_id = team_id
                team_solve_mins[team_id] = math.ceil((submit_time - challenge.start_time)
                                                     / datetime.timedelta(minutes=1))
            else:
                team_wa_count[team_id] = team_wa_count.get(team_id, 0) + 1

        for team_id in team_problem_datas:
            if team_id not in team_submission_id:
                continue
            team_problem_datas[team_id].append(ViewTeamContestScoreboardProblemScoreOutput(
                problem_id=problem_id,
                submit_count=team_submit_count[team_id],
                is_solved=team_id in team_solve_mins,
                solve_time=team_solve_mins.get(team_id, 0),
                is_first=team_id is first_solve_team_id,
                penalty=(service.scoreboard.calculate_penalty(formula=setting_data.penalty_formula,
                                                              solved_time_mins=team_solve_mins[team_id],
                                                              wrong_submissions=team_wa_count.get(team_id, 0))
                         if team_id in team_solve_mins else 0),
                submission_id=team_submission_id[team_id],
            ))

    return [ViewTeamContestScoreboardOutput(
        team_id=team.id,
        team_name=team.name,
        target_problem_data=team_problem_datas[team.id],
        total_penalty=sum(problem_penalty.penalty for problem_penalty in team_problem_datas[team.id]),
        solved_problem_count=sum(team_problem_data.is_solved for team_problem_data in team_problem_datas[team.id]),
    ) for team in teams]


class EditScoreboardInput(BaseModel):
    challenge_label: str = None
    title: str = None
    target_problem_ids: Sequence[int] = None
    penalty_formula: constr(strip_whitespace=True, to_lower=True, strict=True) = None
    team_label_filter: Optional[str] = model.can_omit


@router.patch('/team-contest-scoreboard/{scoreboard_id}')
@enveloped
async def edit_team_contest_scoreboard(scoreboard_id: int, data: EditScoreboardInput) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, scoreboard_id=scoreboard_id):
        raise exc.NoPermission

    if data.penalty_formula and not service.scoreboard.validate_penalty_formula(formula=data.penalty_formula):
        raise exc.InvalidFormula

    await db.scoreboard_setting_team_contest.edit_with_scoreboard(
        scoreboard_id=scoreboard_id, challenge_label=data.challenge_label, title=data.title,
        target_problem_ids=data.target_problem_ids, penalty_formula=data.penalty_formula,
        team_label_filter=data.team_label_filter,
    )
