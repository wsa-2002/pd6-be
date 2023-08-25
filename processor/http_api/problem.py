import io
from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from fastapi import UploadFile, File, BackgroundTasks
from pydantic import BaseModel, PositiveInt

import const
import log
from base import do
from base.enum import RoleType, ChallengePublicizeType, TaskSelectionType, ProblemJudgeType, ReviserSettingType
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from persistence import s3, email
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Problem'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


# TODO: Browse method
@router.get('/problem')
@enveloped
async def browse_problem_set() -> Sequence[do.Problem]:
    """
    ### 權限
    - System normal (not hidden)
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    return await db.problem.browse_problem_set(request_time=context.request_time)


@dataclass
class JudgeSource:
    judge_language: str
    code_uuid: UUID
    filename: str


@dataclass
class ProblemReviser:
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
    reviser_is_enabled: Optional[bool]
    reviser: Optional[ProblemReviser]


@router.get('/problem/{problem_id}')
@enveloped
async def read_problem(problem_id: int) -> ReadProblemOutput:
    """
    ### 權限
    - Class manager (hidden)
    - System normal (not hidden)
    """
    class_role = await service.rbac.get_class_role(context.account.id, problem_id=problem_id)
    is_system_normal = await service.rbac.validate_system(context.account.id, RoleType.normal)

    problem = await db.problem.read(problem_id)
    challenge = await db.challenge.read(problem.challenge_id)
    publicize_time = (challenge.start_time if challenge.publicize_type == ChallengePublicizeType.start_time
                      else challenge.end_time)
    is_challenge_publicized = context.request_time >= publicize_time

    if not (class_role == RoleType.manager
            or (class_role and context.request_time >= challenge.start_time)
            or (is_system_normal and is_challenge_publicized)):
        raise exc.NoPermission

    customized_setting = await db.problem_judge_setting_customized.read(customized_id=problem.setting_id) \
        if problem.judge_type is ProblemJudgeType.customized else None

    reviser_setting = await db.problem_reviser_settings.read_customized(customized_id=problem.reviser_settings[0].id) \
        if problem.reviser_settings else None

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
            judge_language=const.TEMPORARY_CUSTOMIZED_JUDGE_LANGUAGE,
            code_uuid=customized_setting.judge_code_file_uuid,
            filename=customized_setting.judge_code_filename
        ) if problem.judge_type is ProblemJudgeType.customized and class_role is RoleType.manager else None,
        reviser_is_enabled=len(problem.reviser_settings) > 0,
        reviser=ProblemReviser(
            judge_language=const.TEMPORARY_CUSTOMIZED_REVISER_LANGUAGE,
            code_uuid=reviser_setting.judge_code_file_uuid,
            filename=reviser_setting.judge_code_filename,
        ) if problem.reviser_settings and class_role is RoleType.manager else None,
    )


class JudgeSourceInput(BaseModel):
    judge_language: str
    judge_code: str


class CustomizedReviserInput(BaseModel):
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
    reviser_is_enabled: Optional[bool] = model.can_omit
    reviser: Optional[CustomizedReviserInput]
    is_lazy_judge: bool = None


@router.patch('/problem/{problem_id}')
@enveloped
async def edit_problem(problem_id: int, data: EditProblemInput):
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    if ((data.judge_type is ProblemJudgeType.customized and not data.judge_source)
            or (data.judge_type is ProblemJudgeType.normal and data.judge_source)):
        raise exc.IllegalInput

    if data.judge_source and (data.judge_source.judge_language != const.TEMPORARY_CUSTOMIZED_JUDGE_LANGUAGE
                              or not data.judge_source.judge_code):
        raise exc.IllegalInput

    setting_id = None
    if data.judge_source:
        with io.BytesIO(data.judge_source.judge_code.encode(const.JUDGE_CODE_ENCODING)) as file:
            s3_file = await s3.customized_code.upload(file=file)

        s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

        setting_id = await db.problem_judge_setting_customized.add(judge_code_file_uuid=s3_file_uuid,
                                                                   judge_code_filename=str(s3_file_uuid))

    if data.reviser_is_enabled is ...:
        reviser_settings = ...
    elif not data.reviser_is_enabled:
        reviser_settings = []
    else:  # has reviser setting
        if not data.reviser or data.reviser.judge_language != const.TEMPORARY_CUSTOMIZED_REVISER_LANGUAGE \
                or not data.reviser.judge_code:
            raise exc.IllegalInput
        with io.BytesIO(data.reviser.judge_code.encode(const.JUDGE_CODE_ENCODING)) as file:
            s3_file = await s3.customized_code.upload(file=file)
        s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

        reviser_setting_id = await db.problem_reviser_settings.add_customized(judge_code_file_uuid=s3_file_uuid,
                                                                              judge_code_filename=str(s3_file_uuid))
        reviser_settings = [do.ProblemReviserSetting(
            id=reviser_setting_id,
            type=ReviserSettingType.customized,
        )]

    await db.problem.edit(problem_id, challenge_label=data.challenge_label, title=data.title,
                          full_score=data.full_score,
                          description=data.description, io_description=data.io_description, source=data.source,
                          hint=data.hint, setting_id=setting_id, judge_type=data.judge_type,
                          reviser_settings=reviser_settings, is_lazy_judge=data.is_lazy_judge)

    if data.testcase_disabled is not None:
        await db.testcase.disable_enable_testcase_by_problem(problem_id=problem_id,
                                                             testcase_disabled=data.testcase_disabled)


@router.delete('/problem/{problem_id}')
@enveloped
async def delete_problem(problem_id: int):
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    return await db.problem.delete(problem_id=problem_id)


class AddTestcaseInput(BaseModel):
    is_sample: bool
    score: int
    time_limit: PositiveInt
    memory_limit: PositiveInt
    note: Optional[str]
    is_disabled: bool
    label: str


@router.post('/problem/{problem_id}/testcase', tags=['Testcase'])
@enveloped
async def add_testcase_under_problem(problem_id: int, data: AddTestcaseInput) -> model.AddOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    testcase_id = await db.testcase.add(problem_id=problem_id, is_sample=data.is_sample, score=data.score,
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
async def browse_all_testcase_under_problem(problem_id: int) -> Sequence[ReadTestcaseOutput]:
    """
    ### 權限
    - System normal (data without file uuid)
    - CM (all data)
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    is_class_manager = await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id)

    testcases = await db.testcase.browse(problem_id=problem_id, include_disabled=True)
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
async def browse_all_assisting_data_under_problem(problem_id: int) \
        -> Sequence[ReadAssistingDataOutput]:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    result = await db.assisting_data.browse(problem_id=problem_id)
    return [ReadAssistingDataOutput(id=assisting_data.id, problem_id=assisting_data.problem_id,
                                    s3_file_uuid=assisting_data.s3_file_uuid, filename=assisting_data.filename)
            for assisting_data in result]


@router.post('/problem/{problem_id}/assisting-data')
@enveloped
async def add_assisting_data_under_problem(problem_id: int, assisting_data: UploadFile = File(...)) \
        -> model.AddOutput:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    s3_file = await s3.assisting_data.upload(file=assisting_data.file)
    s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    assisting_data_id = await db.assisting_data.add(problem_id=problem_id, s3_file_uuid=s3_file_uuid,
                                                    filename=assisting_data.filename)

    return model.AddOutput(id=assisting_data_id)


@router.post('/problem/{problem_id}/all-assisting-data')
@enveloped
async def download_all_assisting_data(problem_id: int, as_attachment: bool,
                                      background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    async def _task() -> None:
        log.info("Start download all assisting data")

        s3_file = await service.downloader.all_assisting_data(problem_id=problem_id)
        file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                           filename='assisting_data.zip', as_attachment=as_attachment,
                                           expire_secs=const.S3_MANAGER_EXPIRE_SECS)

        log.info("URL signed, sending email")

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=context.account.id)
        await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)

        log.info('Done')
    util.background_task.launch(background_tasks, _task)


@router.post('/problem/{problem_id}/all-sample-testcase')
@enveloped
async def download_all_sample_testcase(problem_id: int, as_attachment: bool,
                                       background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    async def _task() -> None:
        log.info("Start download all sample testcase")

        s3_file = await service.downloader.all_testcase(problem_id=problem_id, is_sample=True)
        file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                           filename='sample_testcase.zip', as_attachment=as_attachment,
                                           expire_secs=const.S3_MANAGER_EXPIRE_SECS)

        log.info("URL signed, sending email")

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=context.account.id)
        await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)

        log.info('Done')

    util.background_task.launch(background_tasks, _task)


@router.post('/problem/{problem_id}/all-non-sample-testcase')
@enveloped
async def download_all_non_sample_testcase(problem_id: int, as_attachment: bool,
                                           background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    async def _task() -> None:
        log.info("Start download all non sample testcase")

        s3_file = await service.downloader.all_testcase(problem_id=problem_id, is_sample=False)
        file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                           filename='non_sample_testcase.zip', as_attachment=as_attachment,
                                           expire_secs=const.S3_MANAGER_EXPIRE_SECS)

        log.info("URL signed, sending email")

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=context.account.id)
        await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)

        log.info('Done')

    util.background_task.launch(background_tasks, _task)


@dataclass
class GetScoreByTypeOutput:
    challenge_type: TaskSelectionType
    score: int


@router.get('/problem/{problem_id}/score')
@enveloped
async def get_score_by_challenge_type_under_problem(problem_id: int) -> GetScoreByTypeOutput:
    """
    ### 權限
    - Self
    """
    problem = await db.problem.read(problem_id)
    challenge = await db.challenge.read(challenge_id=problem.challenge_id)
    submission_judgment = await db.judgment.read_by_challenge_type(problem_id=problem_id,
                                                                   account_id=context.account.id,  # 只能看自己的
                                                                   selection_type=challenge.selection_type,
                                                                   challenge_end_time=challenge.end_time)
    return GetScoreByTypeOutput(challenge_type=challenge.selection_type, score=submission_judgment.score)


@router.get('/problem/{problem_id}/best-score')
@enveloped
async def get_score_by_best_under_problem(problem_id: int) -> GetScoreByTypeOutput:
    """
    ### 權限
    - Self
    """
    problem = await db.problem.read(problem_id)
    # 只能看自己的
    submission_judgment = await db.judgment.get_best_submission_judgment_all_time(problem_id=problem.id,
                                                                                  account_id=context.account.id)
    return GetScoreByTypeOutput(challenge_type=TaskSelectionType.best, score=submission_judgment.score)


@dataclass
class RejudgeProblemOutput:
    submission_count: int


@router.post('/problem/{problem_id}/rejudge')
@enveloped
async def rejudge_problem(problem_id: int) -> RejudgeProblemOutput:
    """
    ### 權限
    - Class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, problem_id=problem_id):
        raise exc.NoPermission

    rejudged_submissions = await service.judge.judge_problem_submissions(problem_id)
    return RejudgeProblemOutput(submission_count=len(rejudged_submissions))


@dataclass
class GetProblemStatOutput:
    solved_member_count: int
    submission_count: int
    member_count: int


@router.get('/problem/{problem_id}/statistics')
@enveloped
async def get_problem_statistics(problem_id: int) -> GetProblemStatOutput:
    """
    ### 權限
    - System normal
    """
    if not await service.rbac.validate_system(context.account.id, RoleType.normal):
        raise exc.NoPermission

    solved_member_count, submission_count, member_count = await service.statistics.get_problem_statistics(
        problem_id=problem_id)
    return GetProblemStatOutput(solved_member_count=solved_member_count,
                                submission_count=submission_count,
                                member_count=member_count)
