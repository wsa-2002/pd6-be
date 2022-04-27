"""
Data Objects
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from base import enum


@dataclass
class Account:
    id: int
    username: str
    nickname: str
    real_name: str
    role: enum.RoleType
    is_deleted: bool
    alternative_email: Optional[str] = None


@dataclass
class Institute:
    id: int
    abbreviated_name: str
    full_name: str
    email_domain: str
    is_disabled: bool


@dataclass
class StudentCard:
    id: int
    institute_id: int
    student_id: str
    email: str
    is_default: bool


@dataclass
class EmailVerification:
    id: int
    email: str
    account_id: int
    institute_id: Optional[int]
    student_id: Optional[str]
    is_consumed: bool


@dataclass
class Course:
    id: int
    name: str
    type: enum.CourseType
    is_deleted: bool


@dataclass
class Class:
    id: int
    name: str
    course_id: int
    is_deleted: bool


@dataclass
class Team:
    id: int
    name: str
    class_id: int
    label: str
    is_deleted: bool


@dataclass
class ClassMember:
    member_id: int
    class_id: int
    role: enum.RoleType


@dataclass
class TeamMember:
    member_id: int
    team_id: int
    role: enum.RoleType


@dataclass
class Grade:
    id: int
    receiver_id: int
    grader_id: int
    class_id: int
    title: str
    score: Optional[str]
    comment: Optional[str]
    update_time: datetime
    is_deleted: bool


@dataclass
class Challenge:
    id: int
    class_id: int
    publicize_type: enum.ChallengePublicizeType
    selection_type: enum.TaskSelectionType
    title: str
    setter_id: int
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_deleted: bool


@dataclass
class ProblemReviserSetting:
    id: int
    type: enum.ReviserSettingType


@dataclass
class Problem:
    id: int
    challenge_id: int
    challenge_label: str
    judge_type: enum.ProblemJudgeType
    setting_id: Optional[int]
    title: str
    setter_id: int
    full_score: Optional[int]
    description: Optional[str]
    io_description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_lazy_judge: bool
    is_deleted: bool
    reviser_settings: Sequence[ProblemReviserSetting]


@dataclass
class ProblemJudgeSettingCustomized:
    id: int
    judge_code_file_uuid: UUID
    judge_code_filename: str


@dataclass
class ProblemReviserSettingCustomized:
    id: int
    judge_code_file_uuid: UUID
    judge_code_filename: str


@dataclass
class Testcase:
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


@dataclass
class S3File:
    uuid: UUID
    bucket: str
    key: str


@dataclass
class SubmissionLanguage:
    id: int
    name: str
    version: str
    is_disabled: bool


@dataclass
class Submission:
    id: int
    account_id: int
    problem_id: int
    language_id: int
    content_file_uuid: UUID
    content_length: int
    filename: str
    submit_time: datetime


@dataclass
class Judgment:
    id: int
    submission_id: int
    verdict: enum.VerdictType
    total_time: int
    max_memory: int
    score: int
    error_message: Optional[str]
    judge_time: datetime


@dataclass
class JudgeCase:
    judgment_id: int
    testcase_id: int
    verdict: enum.VerdictType
    time_lapse: int
    peak_memory: int
    score: int


@dataclass
class Essay:
    id: int
    challenge_id: int
    challenge_label: str
    title: str
    setter_id: int
    description: Optional[str]
    is_deleted: bool


@dataclass
class EssaySubmission:
    id: int
    account_id: int
    essay_id: int
    content_file_uuid: UUID
    filename: str
    submit_time: datetime


@dataclass
class AssistingData:
    id: int
    problem_id: int
    s3_file_uuid: UUID
    filename: str
    is_deleted: bool


@dataclass
class PeerReview:
    id: int
    challenge_id: int
    challenge_label: str
    title: str
    target_problem_id: int
    setter_id: int
    description: str
    min_score: int
    max_score: int
    max_review_count: int
    is_deleted: bool


@dataclass
class PeerReviewRecord:
    id: int
    peer_review_id: int
    grader_id: int
    receiver_id: int
    submission_id: int
    score: Optional[int]
    comment: Optional[str]
    submit_time: Optional[datetime]


@dataclass
class Scoreboard:
    id: int
    challenge_id: int
    challenge_label: str
    title: str
    target_problem_ids: Sequence[int]
    is_deleted: bool
    type: enum.ScoreboardType
    setting_id: int


@dataclass
class ScoreboardSettingTeamProject:
    id: int
    scoring_formula: str
    baseline_team_id: Optional[int]
    rank_by_total_score: bool
    team_label_filter: Optional[str]


@dataclass
class ScoreboardSettingTeamContest:
    id: int
    penalty_formula: str
    team_label_filter: Optional[str]


@dataclass
class Announcement:
    id: int
    title: str
    content: str
    author_id: int
    post_time: datetime
    expire_time: datetime
    is_deleted: bool


@dataclass
class AccessLog:
    id: int
    access_time: datetime
    request_method: str
    resource_path: str
    ip: str
    account_id: Optional[int]
