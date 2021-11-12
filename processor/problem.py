from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from fastapi import UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from base import do
from base.enum import RoleType, ChallengePublicizeType, TaskSelectionType, ProblemJudgeType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import service

from .util import rbac, model

router = APIRouter(
    tags=['Problem'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


# TODO: Browse method
@router.get('/problem')
@enveloped
async def browse_problem_set(request: Request) -> Sequence[do.Problem]:
    """
    ### 權限
    - System normal (not hidden)
    """
    system_role = await rbac.get_role(request.account.id)
    if not system_role >= RoleType.normal:
        raise exc.NoPermission

    return await service.problem.browse_problem_set(request_time=request.time)


@dataclass
class JudgeSource:
    judge_language: str
    code_uuid: UUID
    filename: str


@dataclass
class ReadProblemOutput:
    id: int
    challenge_id: int
    challenge_label: str
    judge_type: ProblemJudgeType
    title: str
    setter_id: int
    full_score: Optional[int]
    description: Optional[str]
    io_description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_deleted: bool
    judge_source: Optional[JudgeSource]


@router.get('/problem/{problem_id}')
@enveloped
async def read_problem(problem_id: int, request: Request) -> ReadProblemOutput:
    """
    ### 權限
    - Class manager (hidden)
    - System normal (not hidden)
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    is_system_normal = await rbac.validate(request.account.id, RoleType.normal)
    class_role = await rbac.get_role(request.account.id, class_id=challenge.class_id)

    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = request.time >= publicize_time

    if not (class_role == RoleType.manager
            or (class_role and request.time >= challenge.start_time)
            or (is_system_normal and is_challenge_publicized)):
        raise exc.NoPermission

    customized_setting = do.ProblemJudgeSettingCustomized
    if problem.judge_type is ProblemJudgeType.customized:
        customized_setting = await service.problem_judge_setting_customized.read(customized_id=problem.setting_id)

    return ReadProblemOutput(
        id=problem.id,
        challenge_id=problem.challenge_id,
        challenge_label=problem.challenge_label,
        title=problem.title,
        judge_type=problem.judge_type,
        setter_id=problem.setter_id,
        full_score=problem.full_score,
        description=problem.description,
        io_description=problem.io_description,
        source=problem.source,
        hint=problem.hint,
        is_deleted=problem.is_deleted,
        judge_source=JudgeSource(
            judge_language="python 3.8",
            code_uuid=customized_setting.judge_code_file_uuid,
            filename=customized_setting.judge_code_filename
        ) if problem.judge_type is ProblemJudgeType.customized and class_role is RoleType.manager else None
    )


class JudgeSourceInput(BaseModel):
    judge_language: str
    judge_code: str


class EditProblemInput(BaseModel):
    challenge_label: str = None
    title: str = None
    full_score: Optional[int] = model.can_omit
    testcase_disabled: bool = None
    description: Optional[str] = model.can_omit
    io_description: Optional[str] = model.can_omit
    source: Optional[str] = model.can_omit
    hint: Optional[str] = model.can_omit
    judge_type: ProblemJudgeType
    judge_source: Optional[JudgeSourceInput]


@router.patch('/problem/{problem_id}')
@enveloped
async def edit_problem(problem_id: int, data: EditProblemInput, request: Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    if ((data.judge_type is ProblemJudgeType.customized and not data.judge_source)
            or (data.judge_type is ProblemJudgeType.normal and data.judge_source)):
        raise exc.IllegalInput

    if data.judge_source and (data.judge_source.judge_language != 'python 3.8' or not data.judge_source.judge_code):
        raise exc.IllegalInput

    return await service.problem.edit(problem_id, challenge_label=data.challenge_label, title=data.title,
                                      full_score=data.full_score, testcase_disabled=data.testcase_disabled,
                                      description=data.description, io_description=data.io_description,
                                      source=data.source, hint=data.hint, judge_type=data.judge_type,
                                      judge_code=data.judge_source.judge_code if data.judge_source else None)


@router.delete('/problem/{problem_id}')
@enveloped
async def delete_problem(problem_id: int, request: Request):
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    return await service.problem.delete(problem_id=problem_id)


class AddTestcaseInput(BaseModel):
    is_sample: bool
    score: int
    time_limit: int
    memory_limit: int
    note: Optional[str]
    is_disabled: bool
    label: str


@router.post('/problem/{problem_id}/testcase', tags=['Testcase'])
@enveloped
async def add_testcase_under_problem(problem_id: int, data: AddTestcaseInput, request: Request) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    testcase_id = await service.testcase.add(problem_id=problem_id, is_sample=data.is_sample, score=data.score,
                                             label=data.label, input_file_uuid=None, output_file_uuid=None,
                                             input_filename=None, output_filename=None,
                                             time_limit=data.time_limit, memory_limit=data.memory_limit,
                                             is_disabled=data.is_disabled, note=data.note)
    return model.AddOutput(id=testcase_id)


@dataclass
class ReadTestcaseOutput:
    id: int
    problem_id: int
    is_sample: bool
    score: int
    label: Optional[str]
    input_file_uuid: Optional[UUID]
    output_file_uuid: Optional[UUID]
    input_filename: Optional[str]
    output_filename: Optional[str]
    note: Optional[str]
    time_limit: int
    memory_limit: int
    is_disabled: bool
    is_deleted: bool


@router.get('/problem/{problem_id}/testcase')
@enveloped
async def browse_all_testcase_under_problem(problem_id: int, request: Request) -> Sequence[ReadTestcaseOutput]:
    """
    ### 權限
    - System normal (data without file uuid)
    - CM (all data)
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    is_class_manager = await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id)

    testcases = await service.testcase.browse(problem_id=problem_id, include_disabled=True)
    return [ReadTestcaseOutput(
        id=testcase.id,
        problem_id=testcase.problem_id,
        is_sample=testcase.is_sample,
        score=testcase.score,
        label=testcase.label,
        input_file_uuid=testcase.input_file_uuid if (testcase.is_sample or is_class_manager) else None,
        output_file_uuid=testcase.output_file_uuid if (testcase.is_sample or is_class_manager) else None,
        input_filename=testcase.input_filename,
        output_filename=testcase.output_filename,
        note=testcase.note,
        time_limit=testcase.time_limit,
        memory_limit=testcase.memory_limit,
        is_disabled=testcase.is_disabled,
        is_deleted=testcase.is_deleted,
    ) for testcase in testcases]


@dataclass
class ReadAssistingDataOutput:
    id: int
    problem_id: int
    s3_file_uuid: UUID
    filename: str


@router.get('/problem/{problem_id}/assisting-data')
@enveloped
async def browse_all_assisting_data_under_problem(problem_id: int, request: Request) \
        -> Sequence[ReadAssistingDataOutput]:
    """
    ### 權限
    - class manager
    """
    problem = await service.problem.read(problem_id=problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    result = await service.assisting_data.browse_with_problem_id(problem_id=problem_id)
    return [ReadAssistingDataOutput(id=assisting_data.id, problem_id=assisting_data.problem_id,
                                    s3_file_uuid=assisting_data.s3_file_uuid, filename=assisting_data.filename)
            for assisting_data in result]


@router.post('/problem/{problem_id}/assisting-data')
@enveloped
async def add_assisting_data_under_problem(problem_id: int, request: Request, assisting_data: UploadFile = File(...)) \
        -> model.AddOutput:
    """
    ### 權限
    - class manager
    """
    problem = await service.problem.read(problem_id=problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    assisting_data_id = await service.assisting_data.add(file=assisting_data.file, filename=assisting_data.filename,
                                                         problem_id=problem_id)
    return model.AddOutput(id=assisting_data_id)


@router.post('/problem/{problem_id}/all-assisting-data')
@enveloped
async def download_all_assisting_data(problem_id: int, request: Request, as_attachment: bool,
                                      background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    problem = await service.problem.read(problem_id=problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission
    background_tasks.add_task(service.assisting_data.download_all,
                              account_id=request.account.id, problem_id=problem_id, as_attachment=as_attachment)
    return


@router.post('/problem/{problem_id}/all-sample-testcase')
@enveloped
async def download_all_sample_testcase(problem_id: int, request: Request, as_attachment: bool,
                                       background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    problem = await service.problem.read(problem_id=problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    background_tasks.add_task(service.testcase.download_all_sample,
                              account_id=request.account.id, problem_id=problem_id, as_attachment=as_attachment)
    return


@router.post('/problem/{problem_id}/all-non-sample-testcase')
@enveloped
async def download_all_non_sample_testcase(problem_id: int, request: Request, as_attachment: bool,
                                           background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    problem = await service.problem.read(problem_id=problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    background_tasks.add_task(service.testcase.download_all_non_sample,
                              account_id=request.account.id, problem_id=problem_id, as_attachment=as_attachment)
    return


@dataclass
class GetScoreByTypeOutput:
    challenge_type: TaskSelectionType
    score: int


@router.get('/problem/{problem_id}/score')
@enveloped
async def get_score_by_challenge_type_under_problem(problem_id: int, request: Request) -> GetScoreByTypeOutput:
    """
    ### 權限
    - Self
    """
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(challenge_id=problem.challenge_id, include_scheduled=True)
    submission_judgment = await service.submission.get_problem_score_by_type(problem_id=problem_id,
                                                                             account_id=request.account.id,  # 只能看自己的
                                                                             selection_type=challenge.selection_type,
                                                                             challenge_end_time=challenge.end_time)
    return GetScoreByTypeOutput(challenge_type=challenge.selection_type, score=submission_judgment.score)


@router.get('/problem/{problem_id}/best-score')
@enveloped
async def get_score_by_best_under_problem(problem_id: int, request: Request) -> GetScoreByTypeOutput:
    """
    ### 權限
    - Self
    """
    problem = await service.problem.read(problem_id)
    # 只能看自己的
    submission_judgment = await service.submission.get_problem_all_time_best_score(problem_id=problem.id,
                                                                                   account_id=request.account.id)
    return GetScoreByTypeOutput(challenge_type=TaskSelectionType.best, score=submission_judgment.score)


@dataclass
class RejudgeProblemOutput:
    submission_count: int


@router.post('/problem/{problem_id}/rejudge')
@enveloped
async def rejudge_problem(problem_id: int, request: Request) -> RejudgeProblemOutput:
    """
    ### 權限
    - Class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    problem = await service.problem.read(problem_id)
    challenge = await service.challenge.read(problem.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    rejudged_submissions = await service.judgment.judge_problem_submissions(problem.id)
    return RejudgeProblemOutput(submission_count=len(rejudged_submissions))


@dataclass
class GetProblemStatOutput:
    solved_member_count: int
    submission_count: int
    member_count: int


@router.get('/problem/{problem_id}/statistics')
@enveloped
async def get_problem_statistics(problem_id: int, request: Request) -> GetProblemStatOutput:
    """
    ### 權限
    - System normal
    """
    if not await rbac.validate(request.account.id, RoleType.normal):
        raise exc.NoPermission

    solved_member_count, submission_count, member_count = await service.problem.get_problem_statistics(problem_id=problem_id)
    return GetProblemStatOutput(solved_member_count=solved_member_count,
                                submission_count=submission_count,
                                member_count=member_count)
