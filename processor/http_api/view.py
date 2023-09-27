from dataclasses import dataclass
from typing import Sequence

from base.enum import RoleType, FilterOperator, VerdictType
from base import popo, vo
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
from persistence import database as db
import service
import util
from util import model
from util.context import context

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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCOUNT_COLUMNS.items()})
async def view_browse_account_with_default_student_id(
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewAccountOutput:
    """
    ### 權限
    - System Manager

    ### Available columns
    """
    is_system_manager = await service.rbac.validate_system(context.account.id, RoleType.manager)
    if not is_system_manager:
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_ACCOUNT_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_ACCOUNT_COLUMNS)

    result, total_count = await db.view.account(limit=limit, offset=offset, filters=filters, sorters=sorters)

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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_MEMBER_COLUMNS.items()})
async def view_browse_class_member(
        class_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewClassMemberOutput:
    """
    ### 權限
    - Class normal
    - Class+ manager

    ### Available columns
    """
    if (not await service.rbac.validate_class(context.account.id, RoleType.normal, class_id=class_id)
            and not await service.rbac.validate_inherit(context.account.id, RoleType.manager, class_id=class_id)):
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_CLASS_MEMBER_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_CLASS_MEMBER_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    result, total_count = await db.view.class_member(limit=limit, offset=offset, filters=filters, sorters=sorters)

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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS.items()})
async def view_browse_submission_under_class(
        class_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewSubmissionUnderClassOutput:
    """
    ### 權限
    - Class manager

    ### Available columns
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_SUBMISSION_UNDER_CLASS_COLUMNS)

    submissions, total_count = await db.view.class_submission(class_id=class_id,
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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_SUBMISSION_COLUMNS.items()})
async def view_browse_submission(account_id: int, limit: model.Limit = 50, offset: model.Offset = 0,
                                 filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewMySubmissionOutput:
    """
    ### 權限
    - Self: see self

    ### Available columns
    """
    if account_id != context.account.id:
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_SUBMISSION_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_SUBMISSION_COLUMNS)

    # 只能看自己的
    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=context.account.id))

    submissions, total_count = await db.view.my_submission(limit=limit, offset=offset,
                                                           filters=filters, sorters=sorters)

    return ViewMySubmissionOutput(submissions, total_count=total_count)


BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS = {
    'submission_id': int,
    'judgment_id': int,
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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS.items()})
async def view_browse_my_submission_under_problem(account_id: int,
                                                  problem_id: int,
                                                  limit: model.Limit = 50, offset: model.Offset = 0,
                                                  filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewMySubmissionUnderProblemOutput:
    """
    ### 權限
    - Self: see self

    ### Available columns
    """
    if account_id != context.account.id:
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_MY_SUBMISSION_UNDER_PROBLEM_COLUMNS)

    # 只能看自己的
    filters.append(popo.Filter(col_name='account_id',
                               op=FilterOperator.eq,
                               value=context.account.id))

    filters.append(popo.Filter(col_name='problem_id',
                               op=FilterOperator.eq,
                               value=problem_id))

    submissions, total_count = await db.view.my_submission_under_problem(limit=limit, offset=offset,
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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_PROBLEM_SET_COLUMNS.items()})
async def view_browse_problem_set_under_class(
        class_id: int,
        limit: model.Limit = 50, offset: model.Offset = 0,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewProblemSetOutput:
    """
    ### 權限
    - System normal (not hidden)

    ### Available columns
    """
    system_role = await service.rbac.get_system_role(context.account.id)
    if not system_role >= RoleType.normal:
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_PROBLEM_SET_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_PROBLEM_SET_COLUMNS)

    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    result, total_count = await db.view.problem_set(limit=limit, offset=offset,
                                                    filters=filters, sorters=sorters, ref_time=context.request_time)
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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_CLASS_GRADE_COLUMNS.items()})
async def view_browse_class_grade(class_id: int,
                                  limit: int = 50, offset: int = 0,
                                  filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewGradeOutput:
    """
    ### 權限
    - Class manager (all)
    - Class normal (self)

    ### Available columns
    """

    filters = util.model.parse_filter(filter, BROWSE_CLASS_GRADE_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_CLASS_GRADE_COLUMNS)
    filters.append(popo.Filter(col_name='class_id',
                               op=FilterOperator.eq,
                               value=class_id))

    if await service.rbac.validate_class(context.account.id, RoleType.manager, class_id=class_id):  # Class manager
        grades, total_count = await db.view.grade(limit=limit, offset=offset, filters=filters, sorters=sorters)
        return ViewGradeOutput(grades, total_count=total_count)
    else:  # Self
        filters.append(popo.Filter(col_name='grade.receiver_id',
                                   op=FilterOperator.eq,
                                   value=context.account.id))

        grades, total_count = await db.view.grade(limit=limit, offset=offset, filters=filters, sorters=sorters)
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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_ACCESS_LOG_COLUMNS.items()})
async def view_browse_access_log(
        limit: model.Limit, offset: model.Offset,
        filter: model.FilterStr = None, sort: model.SorterStr = None,
) -> ViewAccessLogOutput:
    """
    ### 權限
    - Class+ manager

    ### Available columns
    """
    if not (await service.rbac.validate_system(context.account.id, RoleType.manager)  # System manager
            # or await rbac.any_class_role(member_id=context.account.id, role=RoleType.manager)):  # Any class manager
    ):
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_ACCESS_LOG_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_ACCESS_LOG_COLUMNS)

    access_logs, total_count = await db.view.access_log(limit=limit, offset=offset,
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
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_PEER_REVIEW_RECORD_COLUMNS.items()})
async def view_peer_review_summary_review(peer_review_id: int,
                                          limit: model.Limit = 50, offset: model.Offset = 0,
                                          filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewPeerReviewRecordOutput:
    """
    ### 權限
    - Class Manager

    ### Available columns
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, peer_review_id=peer_review_id):
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_PEER_REVIEW_RECORD_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_PEER_REVIEW_RECORD_COLUMNS)

    peer_review_records, total_count = await db.view.view_peer_review_record(peer_review_id=peer_review_id,
                                                                             limit=limit, offset=offset,
                                                                             filters=filters, sorters=sorters,
                                                                             is_receiver=False)
    return ViewPeerReviewRecordOutput(peer_review_records, total_count=total_count)


@router.get('/peer-review/{peer_review_id}/view/receiver-summary')
@enveloped
@util.api_doc.add_to_docstring({k: v.__name__ for k, v in BROWSE_PEER_REVIEW_RECORD_COLUMNS.items()})
async def view_peer_review_summary_receive(peer_review_id: int,
                                           limit: model.Limit = 50, offset: model.Offset = 0,
                                           filter: model.FilterStr = None, sort: model.SorterStr = None) \
        -> ViewPeerReviewRecordOutput:
    """
    ### 權限
    - Class Manager

    ### Available columns
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, peer_review_id=peer_review_id):
        raise exc.NoPermission

    filters = util.model.parse_filter(filter, BROWSE_PEER_REVIEW_RECORD_COLUMNS)
    sorters = util.model.parse_sorter(sort, BROWSE_PEER_REVIEW_RECORD_COLUMNS)

    peer_review_records, total_count = await db.view.view_peer_review_record(peer_review_id=peer_review_id,
                                                                             limit=limit, offset=offset,
                                                                             filters=filters, sorters=sorters,
                                                                             is_receiver=True)

    return ViewPeerReviewRecordOutput(data=peer_review_records, total_count=total_count)
