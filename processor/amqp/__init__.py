from datetime import datetime

import pydantic

import common.do
import log
import persistence.database as db
from util import dtype


async def save_report(body: bytes) -> None:
    log.info('Received save report task')
    report = pydantic.parse_raw_as(common.do.JudgeReport, body.decode())

    # Help ensure data is valid for database
    for judge_case in report.judge_cases:
        judge_case.score = dtype.int32(judge_case.score)
    report.judgment.score = dtype.int32(report.judgment.score)

    judgment_id = await db.judgment.add(
        submission_id=report.judgment.submission_id,
        verdict=report.judgment.verdict,
        total_time=report.judgment.total_time,
        max_memory=report.judgment.max_memory,
        score=report.judgment.score,
        error_message=report.judgment.error_message,
        judge_time=datetime.now(),
    )
    for judge_case in report.judge_cases:
        await db.judgment.add_case(
            judgment_id=judgment_id,
            testcase_id=judge_case.testcase_id,
            verdict=judge_case.verdict,
            score=judge_case.score,
            time_lapse=judge_case.time_lapse,
            peak_memory=judge_case.peak_memory,
        )
