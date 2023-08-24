from dataclasses import dataclass
from typing import Optional, Sequence

from fastapi import BackgroundTasks
from pydantic import BaseModel, constr

import const
import log
from base import do, enum, popo
from base.enum import RoleType, FilterOperator, ChallengePublicizeType, ScoreboardType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from persistence import email, s3
import util
from util import model
from util.context import context

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
async def add_challenge_under_class(class_id: int, data: AddChallengeInput) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    if data.start_time > data.end_time:
        raise exc.IllegalInput

    challenge_id = await db.challenge.add(
        class_id=class_id, publicize_type=data.publicize_type, selection_type=data.selection_type,
        title=data.title, setter_id=context.account.id, description=data.description,
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


class BrowseChallengeUnderclassOutput(model.BrowseOutputBase):
    data: Sequence[do.Challenge]


@router.get('/class/{class_id}/challenge', tags=['Course'])
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_CHALLENGE_COLUMNS.items()})
async def browse_challenge_under_class(
        class_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> BrowseChallengeUnderclassOutput:
    """
    ### 權限
    - Class manager (all)
    - System normal (not scheduled)

    ### Available columns
    """
    system_role = await service.rbac.get_system_role(context.account.id)
    class_role = await service.rbac.get_class_role(context.account.id, class_id=class_id)

    if system_role < RoleType.normal:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CHALLENGE_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CHALLENGE_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    challenges, total_count = await db.challenge.browse(limit=limit, offset=offset, filters=filters,
                                                        sorters=sorters,
                                                        exclude_scheduled=class_role < RoleType.manager,
                                                        ref_time=context.request_time,
                                                        by_publicize_type=True if not class_role else False)

    return BrowseChallengeUnderclassOutput(challenges, total_count=total_count)


@router.get('/challenge/{challenge_id}')
@enveloped
async def read_challenge(challenge_id: int) -> do.Challenge:
    """
    ### 權限
    - Class manager (all)
    - Class normal & guest (after start time)
    - System normal (after scheduled time)
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    challenge = await db.challenge.read(challenge_id=challenge_id, ref_time=context.request_time)
    class_role = await service.rbac.get_class_role(context.account.id, challenge_id=challenge_id)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = context.request_time >= publicize_time

    if not (is_challenge_publicized
            or (class_role and context.request_time >= challenge.start_time)
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
async def edit_challenge(challenge_id: int, data: EditChallengeInput) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    await db.challenge.edit(challenge_id=challenge_id, publicize_type=data.publicize_type,
                            selection_type=data.selection_type,
                            title=data.title, description=data.description, start_time=data.start_time,
                            end_time=data.end_time)


@router.delete('/challenge/{challenge_id}')
@enveloped
async def delete_challenge(challenge_id: int) -> None:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
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
async def add_problem_under_challenge(challenge_id: int, data: AddProblemInput) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    problem_id = await db.problem.add(
        challenge_id=challenge_id, challenge_label=data.challenge_label,
        title=data.title, setter_id=context.account.id, full_score=data.full_score,
        description=data.description, io_description=data.io_description, source=data.source, hint=data.hint,
    )

    return model.AddOutput(id=problem_id)


class AddEssayInput(BaseModel):
    challenge_label: str
    title: str
    description: Optional[str]


@router.post('/challenge/{challenge_id}/essay', tags=['Essay'])
@enveloped
async def add_essay_under_challenge(challenge_id: int, data: AddEssayInput) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    essay_id = await db.essay.add(challenge_id=challenge_id, challenge_label=data.challenge_label,
                                  title=data.title, setter_id=context.account.id, description=data.description)
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
async def add_peer_review_under_challenge(challenge_id: int, data: AddPeerReviewInput) \
        -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    # validate problem belongs to same class
    target_problem = await db.problem.read(problem_id=data.target_problem_id)
    target_problem_challenge = await db.challenge.read(challenge_id=target_problem.challenge_id)

    # Only allow peer review to target to same class
    challenge = await db.challenge.read(challenge_id)
    if challenge.class_id is not target_problem_challenge.class_id:
        raise exc.IllegalInput

    peer_review_id = await db.peer_review.add(challenge_id=challenge_id,
                                              challenge_label=data.challenge_label,
                                              title=data.title,
                                              target_problem_id=data.target_problem_id,
                                              setter_id=context.account.id,
                                              description=data.description,
                                              min_score=data.min_score, max_score=data.max_score,
                                              max_review_count=data.max_review_count)
    return model.AddOutput(id=peer_review_id)


class AddTeamProjectScoreboardInput(BaseModel):
    challenge_label: str
    title: str
    target_problem_ids: Sequence[int]

    # team_project_scoreboard
    scoring_formula: constr(strip_whitespace=True, to_lower=True, strict=True)
    baseline_team_id: Optional[int]
    rank_by_total_score: bool
    team_label_filter: Optional[str]


@router.post('/challenge/{challenge_id}/team-project-scoreboard', tags=['Team Project Scoreboard'])
@enveloped
async def add_team_project_scoreboard_under_challenge(challenge_id: int, data: AddTeamProjectScoreboardInput) \
        -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    if not await service.scoreboard.validate_formula(formula=data.scoring_formula):
        raise exc.InvalidFormula

    scoreboard_id = await db.scoreboard_setting_team_project.add_under_scoreboard(
        challenge_id=challenge_id, challenge_label=data.challenge_label, title=data.title,
        target_problem_ids=data.target_problem_ids,
        type_=ScoreboardType.team_project, scoring_formula=data.scoring_formula, baseline_team_id=data.baseline_team_id,
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
async def browse_all_task_under_challenge(challenge_id: int) -> BrowseTaskOutput:
    """
    ### 權限
    - Class manager (all)
    - Class guest (active/archived challenges)
    - System Normal (by challenge publicize type)
    """
    challenge = await db.challenge.read(challenge_id=challenge_id, ref_time=context.request_time)
    class_role = await service.rbac.get_class_role(context.account.id, challenge_id=challenge_id)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = context.request_time >= publicize_time

    if not ((class_role >= RoleType.guest and context.request_time >= challenge.start_time)  # Class guest
            or (await service.rbac.validate_system(context.account.id,
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
async def browse_all_task_status_under_challenge(challenge_id: int) -> Sequence[ReadStatusOutput]:
    """
    ### 權限
    - Self: see self
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.guest, challenge_id=challenge_id):
        raise exc.NoPermission

    results = await service.task.browse_status(challenge_id, account_id=context.account.id)
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
async def get_challenge_statistics(challenge_id: int) -> GetChallengeStatOutput:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
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


class GetMemberSubmissionStatisticsOutput(model.BrowseOutputBase):
    data: GetMemberSubmissionStatOutput


@router.get('/challenge/{challenge_id}/statistics/member-submission')
@enveloped
async def get_member_submission_statistics(challenge_id: int) -> GetMemberSubmissionStatisticsOutput:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    results = await service.statistics.get_member_submission_statistics(challenge_id=challenge_id)
    member_submission_stat = GetMemberSubmissionStatOutput(
        member=[MemberSubmissionStatOutput(
            id=member_id,
            problem_scores=[ProblemScores(problem_id=problem_id, judgment=judgment) for problem_id, judgment in
                            problem_scores],
            essay_submissions=essays if essays else None)
            for member_id, problem_scores, essays in results])

    return GetMemberSubmissionStatisticsOutput(data=member_submission_stat, total_count=results.__len__())


@router.post('/challenge/{challenge_id}/all-submission')
@enveloped
async def download_all_submissions(challenge_id: int, as_attachment: bool,
                                   background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    async def _task() -> None:
        log.info("Start download all submission")

        challenge = await db.challenge.read(challenge_id)
        s3_file = await service.downloader.all_submissions(challenge_id=challenge_id)
        file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                           expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                                           filename=util.text.get_valid_filename(f'{challenge.title}.zip'),
                                           as_attachment=as_attachment)

        log.info("URL signed, sending email")

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=context.account.id)
        if student_card.email:
            await email.notification.send_file_download_url(to=student_card.email, file_url=file_url,
                                                            subject=f'[PDOGS] All submissions for {challenge.title}')
        if account.alternative_email:
            await email.notification.send_file_download_url(to=account.alternative_email, file_url=file_url,
                                                            subject=f'[PDOGS] All submissions for {challenge.title}')
        log.info('Done')

    util.background_task.launch(background_tasks, _task)


@router.post('/challenge/{challenge_id}/all-plagiarism-report')
@enveloped
async def download_all_plagiarism_reports(challenge_id: int, as_attachment: bool,
                                          background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    async def _task() -> None:
        log.info("Start download all essay submission")

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=context.account.id)

        challenge = await db.challenge.read(challenge_id)
        problems = await db.problem.browse_by_challenge(challenge_id=challenge_id)
        for problem in problems:
            problem_title = challenge.title + ' ' + problem.challenge_label
            log.info(f"Start moss plagiarism report task for {problem_title} {problem.id=}")

            report_url = await service.moss.check_all_submissions_moss(title=problem_title,
                                                                       challenge=challenge, problem=problem)

            log.info(f'send to email for moss {problem_title} {problem.id=}')

            if student_card.email:
                await email.notification.send(to=student_card.email,
                                              subject=f'[PDOGS] Plagiarism report for {problem_title}',
                                              msg=f'Plagiarism report for {problem_title}: {report_url}')
            if account.alternative_email:
                await email.notification.send(to=account.alternative_email,
                                              subject=f'[PDOGS] Plagiarism report for {problem_title}',
                                              msg=f'Plagiarism report for {problem_title}: {report_url}')

            log.info(f'download moss report for {problem_title} {problem.id=} {report_url=}')

            s3_file = await service.downloader.moss_report(report_url=report_url)
            file_url = await s3.tools.sign_url(
                bucket=s3_file.bucket, key=s3_file.key,
                expire_secs=const.S3_MANAGER_EXPIRE_SECS,
                filename=util.text.get_valid_filename(f'{challenge.title}_plagiarism_report.zip'),
                as_attachment=as_attachment,
            )

            log.info("URL signed, sending email")

            if student_card.email:
                await email.notification.send_file_download_url(
                    to=student_card.email,
                    file_url=file_url,
                    subject=f'[PDOGS] Plagiarism report file for {problem_title}',
                )
            if account.alternative_email:
                await email.notification.send_file_download_url(
                    to=account.alternative_email,
                    file_url=file_url,
                    subject=f'[PDOGS] Plagiarism report file for {problem_title}',
                )

            log.info(f"Done for {problem_title} {problem.id=}")

        log.info('Done')

    util.background_task.launch(background_tasks, _task)


class AddTeamContestScoreboardInput(BaseModel):
    challenge_label: str
    title: str
    target_problem_ids: Sequence[int]

    # team_project_scoreboard
    penalty_formula: constr(strip_whitespace=True, to_lower=True, strict=True)
    team_label_filter: Optional[str]


@router.post('/challenge/{challenge_id}/team-contest-scoreboard', tags=['Team Contest Scoreboard'])
@enveloped
async def add_team_contest_scoreboard_under_challenge(challenge_id: int, data: AddTeamContestScoreboardInput) \
        -> model.AddOutput:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, challenge_id=challenge_id):
        raise exc.NoPermission

    if not service.scoreboard.validate_penalty_formula(formula=data.penalty_formula):
        raise exc.InvalidFormula

    scoreboard_id = await db.scoreboard_setting_team_contest.add_under_scoreboard(
        challenge_id=challenge_id, challenge_label=data.challenge_label, title=data.title,
        target_problem_ids=data.target_problem_ids,
        penalty_formula=data.penalty_formula, team_label_filter=data.team_label_filter,
    )

    return model.AddOutput(id=scoreboard_id)
