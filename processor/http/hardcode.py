import datetime
import math
from dataclasses import dataclass
from typing import Sequence

import asyncache
import cachetools

from base.enum import RoleType, ScoreboardType, VerdictType
from config import config
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from util.context import context

router = APIRouter(
    tags=['Hardcode'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@dataclass
class TimeInfo:
    contestTime: int  # seconds
    noMoreUpdate: bool
    timestamp: int


@dataclass
class EachRun:
    team: int
    problem: int
    result: str
    submissionTime: int  # minutes


@dataclass
class ReturnEachRun:
    id: int
    team: int
    problem: int
    result: str
    submissionTime: int  # minutes


@dataclass
class ViewTeamContestScoreboardRunsOutput:
    time: TimeInfo
    runs: Sequence[ReturnEachRun]


@router.get('/hardcode/team-contest-scoreboard/{scoreboard_id}/runs')
@enveloped
@asyncache.cached(cachetools.TTLCache(128, ttl=config.scoreboard_hardcode_ttl))
async def view_team_contest_scoreboard_runs(scoreboard_id: int) -> ViewTeamContestScoreboardRunsOutput:
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
    freeze_time = challenge.end_time - datetime.timedelta(hours=1)
    is_freeze = freeze_time < context.request_time < challenge.end_time
    problem_run_infos = [
        EachRun(team=team_id, problem=problem_id,
                result="Yes" if verdict is VerdictType.accepted else "No - Wrong Answer",
                submissionTime=math.ceil((submit_time - challenge.start_time) / datetime.timedelta(minutes=1)))
        for problem_id in scoreboard.target_problem_ids
        for team_id, submission_id, submit_time, verdict
        in await db.judgment.get_class_all_team_submission_verdict_before_freeze(problem_id=problem_id,
                                                                                 class_id=class_id,
                                                                                 team_ids=[team.id for team in teams],
                                                                                 freeze_time=freeze_time if is_freeze else None)  # noqa
    ]

    # sort it again
    problem_run_infos = sorted(problem_run_infos, key=lambda run: run.submissionTime)

    return ViewTeamContestScoreboardRunsOutput(
        time=TimeInfo(
            contestTime=math.ceil((challenge.end_time - challenge.start_time) / datetime.timedelta(seconds=1)),
            noMoreUpdate=challenge.end_time - datetime.datetime.now() < datetime.timedelta(hours=1),
            timestamp=math.ceil((datetime.datetime.now() - challenge.start_time) / datetime.timedelta(seconds=1)),
        ),
        runs=[ReturnEachRun(
            id=i,
            team=run.team,
            problem=run.problem,
            result=run.result,
            submissionTime=run.submissionTime,
        ) for i, run in enumerate(problem_run_infos)]
    )
