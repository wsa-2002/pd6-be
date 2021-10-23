from dataclasses import dataclass
from typing import Sequence, Optional

from base.enum import RoleType, FilterOperator, VerdictType, ScoreboardType
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
class ViewTeamProjectScoreboardOutput:
    team_id: int
    team_name: str
    total_score: Optional[int]
    target_problem_data: Sequence[vo.ProblemScore]


@router.get('/team-project-scoreboard/view/{scoreboard_id}')
@enveloped
async def view_team_project_scoreboard(scoreboard_id: int, team_id: int, request: Request) -> Sequence[ViewTeamProjectScoreboardOutput]:

    scoreboard, scoreboard_setting_data = await service.scoreboard.read_with_scoreboard_setting_data(scoreboard_id=scoreboard_id)
    if scoreboard.type is not ScoreboardType.team_project:
        raise exc.IllegalInput



    challenge = await service.challenge.read(challenge_id=scoreboard.challenge_id, include_scheduled=True)
    class_ = await service.class_.read(class_id=challenge.class_id)


    team_project_scoreboards = await service.scoreboard_setting_team_project.get_problem_raw_score(
        class_id=class_.id,
        team_label_filter=scoreboard_setting_data.team_label_filter,
        target_problem_ids=scoreboard.target_problem_ids,
        rank_by_total_score=scoreboard_setting_data.rank_by_total_score
    )


    new_scoreboards = await service.scoreboard_setting_team_project.get_problem_customized_score(
        team_project_scoreboards,
        target_problem_ids=scoreboard.target_problem_ids,
        scoring_formula=scoreboard_setting_data.scoring_formula,
        rank_by_total_score=scoreboard_setting_data.rank_by_total_score,
        baseline_team_id=scoreboard_setting_data.baseline_team_id
    )


    result = []

    for team_id, new_scoreboard in new_scoreboards.items():  # team_project_scoreboards.items():
        result.append(ViewTeamProjectScoreboardOutput(
            team_id=new_scoreboard.team_id,
            team_name=new_scoreboard.team_name,
            total_score=new_scoreboard.total_score,
            target_problem_data=[new_scoreboard.target_problem_raw_data[problem_id]
                                 for problem_id in scoreboard.target_problem_ids]
        ))

    return result
