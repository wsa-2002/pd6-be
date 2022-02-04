from dataclasses import dataclass
from typing import NamedTuple, Optional, Sequence

from . import base


# Input


@dataclass
class Problem:
    full_score: Optional[int]


@dataclass
class Submission:
    id: int
    file_url: str


@dataclass
class Testcase:
    id: int
    score: int
    input_file_url: Optional[str]
    output_file_url: Optional[str]
    time_limit: base.MilliSeconds
    memory_limit: base.KiloBytes


@dataclass
class AssistingData:
    file_url: str
    filename: str


@dataclass
class CustomizedJudgeSetting:
    file_url: str


@dataclass
class JudgeTask:
    problem: Problem
    submission: Submission
    testcases: Sequence[Testcase]
    assisting_data: Sequence[AssistingData]
    customized_judge_setting: Optional[CustomizedJudgeSetting]


# Output


@dataclass
class Judgment:
    submission_id: int
    verdict: base.VerdictType
    total_time: base.MilliSeconds
    max_memory: base.KiloBytes
    score: int


@dataclass
class JudgeCase:
    testcase_id: int
    verdict: base.VerdictType
    time_lapse: base.MilliSeconds
    peak_memory: base.KiloBytes
    score: int


@dataclass
class JudgeReport:
    judgment: Judgment
    judge_cases: Sequence[JudgeCase]


class ExecuteResult(NamedTuple):
    stdout: bytes
    stderr: bytes
    exit_code: int
    exit_signal: int
    time_lapse: base.MilliSeconds
    peak_memory: base.KiloBytes
