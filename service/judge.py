from datetime import datetime
from typing import Sequence, Optional
from uuid import UUID

import log
from base import do, enum, popo
import const
import judge_core_common.do as judge_do
import judge_core_common.const as judge_const
import persistence.amqp_publisher as publisher
import persistence.database as db
import persistence.s3 as s3


async def judge_submission(submission_id: int, rejudge=False):
    submission = await db.submission.read(submission_id)
    judge_problem, judge_testcases, judge_assisting_datas, customized_judge_setting = await _prepare_problem(
        submission.problem_id)
    priority = judge_const.PRIORITY_SUBMIT if not rejudge else judge_const.PRIORITY_REJUDGE_SINGLE

    await _judge(submission, judge_problem=judge_problem, priority=priority,
                 judge_testcases=judge_testcases, judge_assisting_datas=judge_assisting_datas,
                 customized_judge_setting=customized_judge_setting)


async def judge_problem_submissions(problem_id: int) -> Sequence[do.Submission]:
    judge_problem, judge_testcases, judge_assisting_datas, customized_judge_setting = await _prepare_problem(problem_id)

    submissions: list[do.Submission] = []
    offset, batch_size = 0, 100
    while True:
        batch_submissions, _ = await db.submission.browse(offset=offset, limit=batch_size, filters=[
            popo.Filter(col_name='problem_id', op=enum.FilterOperator.equal, value=problem_id),
        ], sorters=[])
        if not batch_submissions:
            break
        submissions += batch_submissions
        offset += batch_size

    for submission in submissions:
        await _judge(submission, judge_problem=judge_problem, priority=judge_const.PRIORITY_REJUDGE_BATCH,
                     judge_testcases=judge_testcases, judge_assisting_datas=judge_assisting_datas,
                     customized_judge_setting=customized_judge_setting)

    return submissions


async def _prepare_problem(problem_id: int) -> tuple[
    judge_do.Problem,
    Sequence[judge_do.Testcase],
    Sequence[judge_do.AssistingData],
    Optional[judge_do.CustomizedJudgeSetting],
]:
    problem = await db.problem.read(problem_id)
    testcases = await db.testcase.browse(problem.id, include_disabled=False)
    assisting_datas = await db.assisting_data.browse(problem.id)
    customized_judge_setting = await db.problem_judge_setting_customized.read(problem.setting_id) \
        if problem.judge_type is enum.ProblemJudgeType.customized else None

    judge_problem = judge_do.Problem(
        full_score=problem.full_score,
    )

    judge_testcases = [judge_do.Testcase(
        id=testcase.id,
        score=testcase.score,
        input_file_url=await _sign_file_url(testcase.input_file_uuid, filename=f'{i}.in')
        if testcase.input_file_uuid else None,
        output_file_url=await _sign_file_url(testcase.output_file_uuid, filename=f'{i}.out')
        if testcase.output_file_uuid else None,
        time_limit=testcase.time_limit,
        memory_limit=testcase.memory_limit,
    ) for i, testcase in enumerate(testcases)]

    judge_assisting_datas = [judge_do.AssistingData(
        file_url=await _sign_file_url(assisting_data.s3_file_uuid, filename=assisting_data.filename),
        filename=assisting_data.filename,
    ) for assisting_data in assisting_datas]

    customized_judge_setting = judge_do.CustomizedJudgeSetting(await _sign_file_url(
        customized_judge_setting.judge_code_file_uuid,
        filename=customized_judge_setting.judge_code_filename)) \
        if problem.judge_type is enum.ProblemJudgeType.customized else None

    return judge_problem, judge_testcases, judge_assisting_datas, customized_judge_setting


async def _judge(submission: do.Submission, judge_problem: judge_do.Problem, priority: int,
                 customized_judge_setting: Optional[do.ProblemJudgeSettingCustomized],
                 judge_testcases: Sequence[judge_do.Testcase], judge_assisting_datas: Sequence[judge_do.AssistingData]):
    submission_language = await db.submission.read_language(submission.language_id)
    if submission_language.is_disabled:
        log.info(f"Submission id {submission.id} is skipped judge because"
                 f" submission language id {submission.language_id} is disabled")
        return

    await publisher.judge.send_judge(judge_do.JudgeTask(
        problem=judge_problem,
        submission=judge_do.Submission(
            id=submission.id,
            file_url=await _sign_file_url(submission.content_file_uuid, filename=submission.filename),
        ),
        testcases=judge_testcases,
        assisting_data=judge_assisting_datas,
        customized_judge_setting=customized_judge_setting,
    ), language_queue_name=await db.submission.read_language_queue_name(submission_language.id),
        priority=priority)


async def _sign_file_url(uuid: UUID, filename: str):
    return await s3.tools.sign_url_from_do(
        s3_file=await db.s3_file.read(uuid),
        expire_secs=const.S3_EXPIRE_SECS,
        filename=filename,
        as_attachment=True,
    )
