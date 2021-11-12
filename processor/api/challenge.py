from dataclasses import dataclass
from typing import Optional, Sequence

from fastapi import BackgroundTasks
from pydantic import BaseModel

import log
from base import do, enum, popo
from base.enum import RoleType, FilterOperator, ChallengePublicizeType, ScoreboardType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import service
from util.api_doc import add_to_docstring

from processor.util import model

router = APIRouter(
    tags=['Challenge'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


class AddChallengeInput(BaseModel):
    publicize_type: enum.ChallengePublicizeType
    selection_type: enum.TaskSelectionType
    title: str
    description: Optional[str]
    start_time: model.ServerTZDatetime
    end_time: model.ServerTZDatetime


@router.post('/class/{class_id}/challenge', tags=['Course'])
@enveloped
async def add_challenge_under_class(class_id: int, data: AddChallengeInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    if data.start_time > data.end_time:
        raise exc.IllegalInput

    challenge_id = await db.challenge.add(
        class_id=class_id, publicize_type=data.publicize_type, selection_type=data.selection_type,
        title=data.title, setter_id=request.account.id, description=data.description,
        start_time=data.start_time, end_time=data.end_time
    )
    return model.AddOutput(id=challenge_id)


BROWSE_CHALLENGE_COLUMNS = {
    'id': int,
    'class_id': int,
    'publicize_type': enum.ChallengePublicizeType,
    'selection_type': enum.TaskSelectionType,
    'title': str,
    'setter_id': int,
    'description': str,
    'start_time': model.ServerTZDatetime,
    'end_time': model.ServerTZDatetime,
    'is_deleted': bool,
}


@router.get('/class/{class_id}/challenge', tags=['Course'])
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_CHALLENGE_COLUMNS.items()})
async def browse_challenge_under_class(
        class_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> model.BrowseOutputBase:
    """
    ### 權限
    - Class manager (all)
    - System normal (not scheduled)

    ### Available columns
    """
    system_role = await service.rbac.get_role(request.account.id)
    class_role = await service.rbac.get_role(request.account.id, class_id=class_id)

    if system_role < RoleType.normal:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CHALLENGE_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CHALLENGE_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    challenges, total_count = await db.challenge.browse(limit=limit, offset=offset, filters=filters,
                                                        sorters=sorters,
                                                        include_scheduled=(class_role == RoleType.manager),
                                                        ref_time=request.time,
                                                        by_publicize_type=True if not class_role else False)

    return model.BrowseOutputBase(challenges, total_count=total_count)


@router.get('/challenge/{challenge_id}')
@enveloped
async def read_challenge(challenge_id: int, request: Request) -> do.Challenge:
    """
    ### 權限
    - Class manager (all)
    - Class normal & guest (after start time)
    - System normal (after scheduled time)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    if not await service.rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await service.rbac.get_role(request.account.id, class_id=challenge.class_id)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = request.time >= publicize_time

    if not (is_challenge_publicized
            or (class_role and request.time >= challenge.start_time)
            or class_role == RoleType.manager):
        raise exc.NoPermission

    return challenge


class EditChallengeInput(BaseModel):
    # class_id: int
    publicize_type: enum.ChallengePublicizeType = None
    selection_type: enum.TaskSelectionType = None
    title: str = None
    description: Optional[str] = model.can_omit
    start_time: model.ServerTZDatetime = None
    end_time: model.ServerTZDatetime = None


@router.patch('/challenge/{challenge_id}')
@enveloped
async def edit_challenge(challenge_id: int, data: EditChallengeInput, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.challenge.edit(challenge_id=challenge_id, publicize_type=data.publicize_type,
                            selection_type=data.selection_type,
                            title=data.title, description=data.description, start_time=data.start_time,
                            end_time=data.end_time)


@router.delete('/challenge/{challenge_id}')
@enveloped
async def delete_challenge(challenge_id: int, request: Request) -> None:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.challenge.delete(challenge_id)


class AddProblemInput(BaseModel):
    challenge_label: str
    title: str
    full_score: Optional[int]
    description: Optional[str]
    io_description: Optional[str]
    source: Optional[str]
    hint: Optional[str]


@router.post('/challenge/{challenge_id}/problem', tags=['Problem'])
@enveloped
async def add_problem_under_challenge(challenge_id: int, data: AddProblemInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    problem_id = await db.problem.add(
        challenge_id=challenge_id, challenge_label=data.challenge_label,
        title=data.title, setter_id=request.account.id, full_score=data.full_score,
        description=data.description, io_description=data.io_description, source=data.source, hint=data.hint,
    )

    return model.AddOutput(id=problem_id)


class AddEssayInput(BaseModel):
    challenge_label: str
    title: str
    description: Optional[str]


@router.post('/challenge/{challenge_id}/essay', tags=['Essay'])
@enveloped
async def add_essay_under_challenge(challenge_id: int, data: AddEssayInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    essay_id = await db.essay.add(challenge_id=challenge_id, challenge_label=data.challenge_label,
                                  title=data.title, setter_id=request.account.id, description=data.description)
    return model.AddOutput(id=essay_id)


class AddPeerReviewInput(BaseModel):
    challenge_label: str
    title: str
    target_problem_id: int
    description: str
    min_score: int
    max_score: int
    max_review_count: int


@router.post('/challenge/{challenge_id}/peer-review', tags=['Peer Review'])
@enveloped
async def add_peer_review_under_challenge(challenge_id: int, data: AddPeerReviewInput, request: Request) \
        -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    # validate problem belongs to same class
    target_problem = await db.problem.read(problem_id=data.target_problem_id)
    target_problem_challenge = await db.challenge.read(challenge_id=target_problem.challenge_id,
                                                       include_scheduled=True)

    # Only allow peer review to target to same class
    if challenge.class_id is not target_problem_challenge.class_id:
        raise exc.IllegalInput

    peer_review_id = await db.peer_review.add(challenge_id=challenge_id,
                                              challenge_label=data.challenge_label,
                                              title=data.title,
                                              target_problem_id=data.target_problem_id,
                                              setter_id=request.account.id,
                                              description=data.description,
                                              min_score=data.min_score, max_score=data.max_score,
                                              max_review_count=data.max_review_count)
    return model.AddOutput(id=peer_review_id)


class AddTeamProjectScoreboardInput(BaseModel):
    challenge_label: str
    title: str
    target_problem_ids: Sequence[int]

    # team_project_scoreboard
    scoring_formula: str
    baseline_team_id: Optional[int]
    rank_by_total_score: bool
    team_label_filter: Optional[str]


@router.post('/challenge/{challenge_id}/team-project-scoreboard', tags=['Team Project Scoreboard'])
@enveloped
async def add_team_project_scoreboard_under_challenge(challenge_id: int, data: AddTeamProjectScoreboardInput,
                                                      request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    scoreboard_id = await db.scoreboard_setting_team_project.add_under_scoreboard(
        challenge_id=challenge_id, challenge_label=data.challenge_label, title=data.title,
        target_problem_ids=data.target_problem_ids,
        type=ScoreboardType.team_project, scoring_formula=data.scoring_formula, baseline_team_id=data.baseline_team_id,
        rank_by_total_score=data.rank_by_total_score, team_label_filter=data.team_label_filter,
    )

    return model.AddOutput(id=scoreboard_id)


@dataclass
class BrowseTaskOutput:
    problem: Sequence[do.Problem]
    peer_review: Optional[Sequence[do.PeerReview]]
    essay: Optional[Sequence[do.Essay]]
    scoreboard: Optional[Sequence[do.Scoreboard]]


@router.get('/challenge/{challenge_id}/task')
@enveloped
async def browse_all_task_under_challenge(challenge_id: int, request: Request) -> BrowseTaskOutput:
    """
    ### 權限
    - Class manager (all)
    - Class guest (active/archived challenges)
    - System Normal (by challenge publicize type)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await service.rbac.get_role(request.account.id, class_id=challenge.class_id)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = request.time >= publicize_time

    if not ((class_role >= RoleType.guest and request.time >= challenge.start_time)  # Class guest
            or (await service.rbac.validate(request.account.id,
                                            RoleType.normal) and is_challenge_publicized)  # System normal
            or class_role == RoleType.manager):  # Class manager
        raise exc.NoPermission

    problems, peer_reviews, essays, scoreboard = await service.task.browse(challenge.id)

    return BrowseTaskOutput(
        problem=problems,
        peer_review=peer_reviews if class_role else [],
        essay=essays if class_role else [],
        scoreboard=scoreboard if class_role else [],
    )


@dataclass
class ReadProblemStatusOutput:
    problem_id: int
    submission_id: int


@dataclass
class ReadStatusOutput:
    problem: Sequence[ReadProblemStatusOutput]


@router.get('/challenge/{challenge_id}/task-status')
@enveloped
async def browse_all_task_status_under_challenge(challenge_id: int, request: Request) -> Sequence[ReadStatusOutput]:
    """
    ### 權限
    - Self: see self
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id=challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await service.rbac.get_role(request.account.id, class_id=challenge.class_id)
    if class_role < RoleType.guest:
        raise exc.NoPermission

    results = await service.task.browse_status(challenge.id, request.account.id)
    return [ReadStatusOutput(problem=[ReadProblemStatusOutput(problem_id=problem.id, submission_id=submission.id)
                                      for (problem, submission) in results])]


@dataclass
class ProblemStatOutput:
    task_label: str
    solved_member_count: int
    submission_count: int
    member_count: int


@dataclass
class GetChallengeStatOutput:
    tasks: Sequence[ProblemStatOutput]


@router.get('/challenge/{challenge_id}/statistics/summary')
@enveloped
async def get_challenge_statistics(challenge_id: int, request: Request) -> GetChallengeStatOutput:
    """
    ### 權限
    - class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id, include_scheduled=True)
    if not service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    result = await service.statistics.get_challenge_statistics(challenge_id=challenge_id)
    return GetChallengeStatOutput(tasks=[ProblemStatOutput(task_label=task_label,
                                                           solved_member_count=solved_member_count,
                                                           submission_count=submission_count,
                                                           member_count=member_count)
                                         for task_label, solved_member_count, submission_count, member_count in result])


@dataclass
class ProblemScores:
    problem_id: int
    judgment: do.Judgment


@dataclass
class MemberSubmissionStatOutput:
    id: int
    problem_scores: Optional[Sequence[ProblemScores]]
    essay_submissions: Optional[Sequence[do.EssaySubmission]]


@dataclass
class GetMemberSubmissionStatOutput:
    member: Sequence[MemberSubmissionStatOutput]


@router.get('/challenge/{challenge_id}/statistics/member-submission')
@enveloped
async def get_member_submission_statistics(challenge_id: int, request: Request) -> model.BrowseOutputBase:
    """
    ### 權限
    - class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    challenge = await db.challenge.read(challenge_id, include_scheduled=True)
    if not service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    results = await service.statistics.get_member_submission_statistics(challenge_id=challenge.id)
    member_submission_stat = GetMemberSubmissionStatOutput(
        member=[MemberSubmissionStatOutput(
            id=member_id,
            problem_scores=[ProblemScores(problem_id=problem_id, judgment=judgment) for problem_id, judgment in
                            problem_scores],
            essay_submissions=essays if essays else None)
            for member_id, problem_scores, essays in results])

    return model.BrowseOutputBase(data=member_submission_stat, total_count=results.__len__())


@router.post('/challenge/{challenge_id}/all-submission')
@enveloped
async def download_all_submissions(challenge_id: int, request: Request, as_attachment: bool,
                                   background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    challenge = await db.challenge.read(challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    async def background_task(*args, **kwargs):
        try:
            await service.downloader.all_submissions(*args, **kwargs)
        except Exception as e:
            log.exception(e)

    background_tasks.add_task(background_task,
                              account_id=request.account.id, challenge_id=challenge.id, as_attachment=as_attachment)
    return


@router.post('/challenge/{challenge_id}/all-plagiarism-report')
@enveloped
async def download_all_plagiarism_reports(challenge_id: int, request: Request, as_attachment: bool,
                                          background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    challenge = await db.challenge.read(challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    async def background_task(*args, **kwargs):
        try:
            await service.moss.check_all_submissions_moss(*args, **kwargs)
        except Exception as e:
            log.exception(e)

    background_tasks.add_task(background_task,
                              account_id=request.account.id, challenge_id=challenge.id, as_attachment=as_attachment)
    return
