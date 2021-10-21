from dataclasses import dataclass
from typing import Sequence, Optional

from base.enum import RoleType, FilterOperator, VerdictType
from base import popo, vo
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service
from util.api_doc import add_to_docstring

from .util import rbac, model

router = APIRouter(
    tags=['View'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


BROWSE_ACCOUNT_COLUMNS = {
    'account_id': int,
    'username': str,
    'real_name': str,
    'student_id': str,
}


@dataclass
class ViewAccountOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewAccount]


@router.get('/view/account')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCOUNT_COLUMNS.items()})
async def browse_account_with_default_student_id(
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewAccountOutput:
    """
    ### 權限
    - System Manager

    ### Available columns
    """
    is_manager = await rbac.validate(request.account.id, RoleType.manager)
    if not is_manager:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ACCOUNT_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ACCOUNT_COLUMNS)

    result, total_count = await service.view.account(limit=limit, offset=offset, filters=filters, sorters=sorters)

    return ViewAccountOutput(result, total_count=total_count)


BROWSE_CLASS_MEMBER_COLUMNS = {
    'account_id': int,
    'username': str,
    'student_id': str,
    'real_name': str,
    'abbreviated_name': str,
    'role': RoleType,
    'class_id': int,
}


@dataclass
class ViewClassMemberOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewClassMember]


@router.get('/class/{class_id}/view/member')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_MEMBER_COLUMNS.items()})
async def browse_class_member(
        class_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewClassMemberOutput:
    """
    ### 權限
    - Class normal
    - Class+ manager

    ### Available columns
    """
    if (not await rbac.validate(request.account.id, RoleType.normal, class_id=class_id)
            and not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id, inherit=True)):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_CLASS_MEMBER_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_MEMBER_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    result, total_count = await service.view.class_member(limit=limit, offset=offset, filters=filters, sorters=sorters)

    return ViewClassMemberOutput(result, total_count=total_count)


BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS = {
    'submission_id': int,
    'account_id': int,
    'username': str,
    'student_id': str,
    'real_name': str,
    'challenge_id': int,
    'challenge_title': str,
    'problem_id': int,
    'challenge_label': str,
    'verdict': VerdictType,
    'submit_time': model.ServerTZDatetime,
    'class_id': int,
}


@dataclass
class ViewSubmissionUnderClassOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewSubmissionUnderClass]


@router.get('/class/{class_id}/view/submission')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS.items()})
async def browse_submission_under_class(
        class_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewSubmissionUnderClassOutput:
    """
    ### 權限
    - Class manager

    ### Available columns
    """
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)

    submissions, total_count = await service.view.class_submission(class_id=class_id,
                                                                   limit=limit, offset=offset,
                                                                   filters=filters, sorters=sorters)
    return ViewSubmissionUnderClassOutput(submissions, total_count=total_count)


BROWSE_SUBMISSION_COLUMNS = {
    'submission_id': int,
    'course_id': int,
    'course_name': str,
    'class_id': int,
    'class_name': str,
    'challenge_id': int,
    'challenge_title': str,
    'problem_id': int,
    'challenge_label': str,
    'verdict': VerdictType,
    'submit_time': model.ServerTZDatetime,
    'account_id': int,
}


@dataclass
class ViewMySubmissionOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewMySubmission]


@router.get('/view/my-submission')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_COLUMNS.items()})
async def browse_submission(account_id: int, request: Request, limit: model.Limit = 50, offset: model.Offset = 0,
                            filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewMySubmissionOutput:
    """
    ### 權限
    - Self: see self

    ### Available columns
    """
    if account_id != request.account.id:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_SUBMISSION_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_SUBMISSION_COLUMNS)

    # 只能看自己的
    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=request.account.id))

    submissions, total_count = await service.view.my_submission(limit=limit, offset=offset,
                                                                filters=filters, sorters=sorters)

    return ViewMySubmissionOutput(submissions, total_count=total_count)


BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS = {
    'submission_id': int,
    'verdict': VerdictType,
    'score': int,
    'total_time': int,
    'max_memory': int,
    'submit_time': model.ServerTZDatetime,
    'account_id': int,
    'problem_id': int,
}


@dataclass
class ViewMySubmissionUnderProblemOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewMySubmissionUnderProblem]


@router.get('/problem/{problem_id}/view/my-submission')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS.items()})
async def browse_my_submission_under_problem(account_id: int,
                                             problem_id: int,
                                             request: Request,
                                             limit: model.Limit = 50, offset: model.Offset = 0,
                                             filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewMySubmissionUnderProblemOutput:
    """
    ### 權限
    - Self: see self

    ### Available columns
    """
    if account_id != request.account.id:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS)

    # 只能看自己的
    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=request.account.id))

    filters.append(popo.Filter(col_name='problem_id',
                               op=FilterOperator.eq,
                               value=problem_id))

    submissions, total_count = await service.view.my_submission_under_problem(limit=limit, offset=offset,
                                                                              filters=filters, sorters=sorters)

    return ViewMySubmissionUnderProblemOutput(submissions, total_count=total_count)


BROWSE_PROBLEM_SET_COLUMNS = {
    'challenge_id': int,
    'challenge_title': str,
    'problem_id': int,
    'challenge_label': str,
    'problem_title': str,
    'class_id': int,
}


@dataclass
class ViewProblemSetOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewProblemSet]


@router.get('/class/{class_id}/view/problem-set')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_PROBLEM_SET_COLUMNS.items()})
async def browse_problem_set_under_class(
        class_id: int,
        request: Request,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewProblemSetOutput:
    """
    ### 權限
    - System normal (not hidden)

    ### Available columns
    """
    system_role = await rbac.get_role(request.account.id)
    if not system_role >= RoleType.normal:
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_PROBLEM_SET_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_PROBLEM_SET_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    result, total_count = await service.view.problem_set(limit=limit, offset=offset,
                                                         filters=filters, sorters=sorters, ref_time=request.time)
    return ViewProblemSetOutput(result, total_count=total_count)


BROWSE_CLASS_GRADE_COLUMNS = {
    'account_id': int,
    'username': str,
    'student_id': str,
    'real_name': str,
    'title': str,
    'score': str,
    'update_time': model.ServerTZDatetime,
    'grade_id': int,
    'class_id': int,
}


@dataclass
class ViewGradeOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewGrade]


@router.get('/class/{class_id}/view/grade')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_GRADE_COLUMNS.items()})
async def browse_class_grade(class_id: int, request: Request,
                             limit: int = 50, offset: int = 0,
                             filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewGradeOutput:
    """
    ### 權限
    - Class manager (all)
    - Class normal (self)

    ### Available columns
    """

    filters = model.parse_filter(filter, BROWSE_CLASS_GRADE_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_CLASS_GRADE_COLUMNS)
    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    if await rbac.validate(request.account.id, RoleType.manager, class_id=class_id):  # Class manager
        grades, total_count = await service.view.grade(limit=limit, offset=offset, filters=filters, sorters=sorters)
        return ViewGradeOutput(grades, total_count=total_count)
    else:  # Self
        filters.append(popo.Filter(col_name='account_id',
                                   op=FilterOperator.eq,
                                   value=request.account.id))

        grades, total_count = await service.view.grade(limit=limit, offset=offset, filters=filters, sorters=sorters)
        return ViewGradeOutput(grades, total_count=total_count)


BROWSE_ACCESS_LOG_COLUMNS = {
    'account_id': int,
    'username': str,
    'student_id': str,
    'real_name': str,
    'ip': str,
    'resource_path': str,
    'request_method': str,
    'access_time': model.ServerTZDatetime,
    'access_log_id': int,
}


@dataclass
class ViewAccessLogOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewAccessLog]


@router.get('/view/access-log')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCESS_LOG_COLUMNS.items()})
async def browse_access_log(
        req: Request,
        limit: model.Limit, offset: model.Offset,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewAccessLogOutput:
    """
    ### 權限
    - Class+ manager

    ### Available columns
    """
    if not (await rbac.validate(req.account.id, RoleType.manager)  # System manager
            # or await rbac.any_class_role(member_id=req.account.id, role=RoleType.manager)):  # Any class manager
    ):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_ACCESS_LOG_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_ACCESS_LOG_COLUMNS)

    access_logs, total_count = await service.view.access_log(limit=limit, offset=offset,
                                                             filters=filters, sorters=sorters)
    return ViewAccessLogOutput(access_logs, total_count=total_count)


BROWSE_PEER_REVIEW_RECORD_COLUMNS = {
    'username': str,
    'real_name': str,
    'student_id': str,
    'average_score': float,
}


@dataclass
class ViewPeerReviewRecordOutput(model.BrowseOutputBase):
    data: Sequence[vo.ViewPeerReviewRecord]


@router.get('/peer-review/{peer_review_id}/view/reviewer-summary')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_PEER_REVIEW_RECORD_COLUMNS.items()})
async def peer_review_summary_review(peer_review_id: int, request: Request,
                                     limit: model.Limit = 50, offset: model.Offset = 0,
                                     filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewPeerReviewRecordOutput:
    """
    ### 權限
    - Class Manager

    ### Available columns
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await service.peer_review.read(peer_review_id)
    challenge = await service.challenge.read(peer_review.challenge_id, include_scheduled=True)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_PEER_REVIEW_RECORD_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_PEER_REVIEW_RECORD_COLUMNS)

    peer_review_records, total_count = await service.view.view_peer_review_record(peer_review_id=peer_review.id,
                                                                                  limit=limit, offset=offset,
                                                                                  filters=filters, sorters=sorters,
                                                                                  is_receiver=False)
    return ViewPeerReviewRecordOutput(peer_review_records, total_count=total_count)


@router.get('/peer-review/{peer_review_id}/view/receiver-summary')
@enveloped
@add_to_docstring({k: v.__name__ for k, v in BROWSE_PEER_REVIEW_RECORD_COLUMNS.items()})
async def peer_review_summary_receive(peer_review_id: int, request: Request,
                                      limit: model.Limit = 50, offset: model.Offset = 0,
                                      filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewPeerReviewRecordOutput:
    """
    ### 權限
    - Class Manager

    ### Available columns
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    peer_review = await service.peer_review.read(peer_review_id)
    challenge = await service.challenge.read(peer_review.challenge_id, include_scheduled=True)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    filters = model.parse_filter(filter, BROWSE_PEER_REVIEW_RECORD_COLUMNS)
    sorters = model.parse_sorter(sort, BROWSE_PEER_REVIEW_RECORD_COLUMNS)

    peer_review_records, total_count = await service.view.view_peer_review_record(peer_review_id=peer_review.id,
                                                                                  limit=limit, offset=offset,
                                                                                  filters=filters, sorters=sorters,
                                                                                  is_receiver=True)

    return ViewPeerReviewRecordOutput(data=peer_review_records, total_count=total_count)


import persistence.database as db

# ------------WIP---------------
@dataclass
class TeamProjectProblemScore:
    problem_id: int
    score: int
    submission_id: int

@dataclass
class ViewTeamProjectScoreboardOutput:
    team_id: int
    team_name: str
    total_score: Optional[int]
    target_problem_data: Sequence[TeamProjectProblemScore]


@router.get('/team-project-scoreboard/view/{scoreboard_id}')
@enveloped
async def view_team_project_scoreboard(scoreboard_id: int, team_id: int, request: Request) -> Sequence[ViewTeamProjectScoreboardOutput]:

    scoreboard, scoreboard_setting_data = await service.scoreboard.read_with_scoreboard_setting_data(scoreboard_id=scoreboard_id)
    # if scoreboard.type is not enum.team_project: IllegalInput

    team_project_scoreboards = []
    team = await service.team.read(team_id=team_id)
    team_members = await service.team.browse_members(team_id=team.id)  # Sequence[do.TeamMembers]
    team_member_ids = [team_member.member_id for team_member in team_members]

    target_problem_data = []
    total_score = 0
    for target_problem_id in scoreboard.target_problem_ids:

        problem = await service.problem.read(problem_id=target_problem_id)

        problem_normal, submission, judgment = await db.scoreboard_setting_team_project.\
                get_problem_normal_score(problem_id=problem.id, team_member_ids=team_member_ids)

        total_score += judgment.score
        target_problem_data.append(TeamProjectProblemScore(problem_id=problem_normal.id,
                                                           score=judgment.id,
                                                           submission_id=submission.id))



    # TODO: change team_project_scoreboards from LIST to SEQUENCE
    team_project_scoreboards.append(ViewTeamProjectScoreboardOutput(
        team_id=team.id,
        team_name=team.name,
        total_score=total_score if scoreboard_setting_data.rank_by_total_score else None,
        target_problem_data=target_problem_data)
    )

    return [ViewTeamProjectScoreboardOutput(
        team_id=team_project_scoreboard.team_id,
        team_name=team_project_scoreboard.team_name,
        total_score=team_project_scoreboard.total_score,
        target_problem_data=target_problem_data,
    ) for team_project_scoreboard in team_project_scoreboards]




# @router.get('/team-project-scoreboard/view/{scoreboard_id}')
# @enveloped
# async def view_team_project_scoreboard(scoreboard_id: int, request: Request) -> ViewGradeOutput:
#
#     scoreboard, scoreboard_setting_data = await service.scoreboard.read_with_scoreboard_setting_data(scoreboard_id=scoreboard_id)
#     # if scoreboard.type is not enum.team_project: IllegalInput
#
#
#     # TODO: move to service layer
#     teams = await db.scoreboard_setting_team_project.browse_filtered_team_under_class(scoreboard_id=scoreboard_id)
#     # teams: Sequence[do.Team]
#
#
#     team_project_scoreboards = []
#     for team in teams:
#         team_members = await service.team.browse_members(team_id=team.id)  # Sequence[do.TeamMembers]
#         team_member_ids = [team_member.member_id for team_member in team_members]
#
#         target_problem_data = []
#         total_score = 0
#         for target_problem_id in scoreboard.target_problem_ids:
#
#             problem = await service.problem.read(problem_id=target_problem_id)
#
#             if problem.judge_type is enum.ProblemJudgeType.normal:
#                 problem_normal_score = await db.scoreboard_setting_team_project.\
#                     get_problem_normal_score(problem_id=problem.id, team_member_ids=team_member_ids)
#
#                 total_score += problem_normal_score.score
#                 target_problem_data.append(problem_normal_score)
#
#             elif problem.judge_type is enum.ProblemJudgeType.customized:
#                 problem_customized_score = await db.scoreboard_setting_team_project.\
#                     get_problem_customized_score(problem_id=problem.id, team_member_ids=team_member_ids)
#
#                 total_score += problem_customized_score.score
#                 target_problem_data.append(problem_customized_score)
#
#         # TODO: change team_project_scoreboards from LIST to SEQUENCE
#         team_project_scoreboards.append(ViewTeamProjectScoreboardOutput(
#             team_id=team.id,
#             team_name=team.name,
#             total_score=total_score if scoreboard_setting_data.rank_by_total_score else None,
#             target_problem_data=target_problem_data)
#         )
#
#     return [ViewTeamProjectScoreboardOutput(
#         team_id=team_project_scoreboard.team_id,
#         team_name=team_project_scoreboard.team_name,
#         total_score=team_project_scoreboard.total_score,
#     ) for team_project_scoreboard in team_project_scoreboards]