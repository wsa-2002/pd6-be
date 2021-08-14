"""
Data Objects
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
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
    score: Optional[int]
    comment: Optional[str]
    update_time: datetime
    is_deleted: bool


@dataclass
class Challenge:
    id: int
    class_id: int
    type: enum.ChallengeType
    publicize_type: enum.ChallengePublicizeType
    title: str
    setter_id: int
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_deleted: bool


@dataclass
class Problem:
    id: int
    challenge_id: int
    challenge_label: str
    selection_type: enum.TaskSelectionType
    title: str
    setter_id: int
    full_score: int
    description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_deleted: bool


@dataclass
class Testcase:
    id: int
    problem_id: int
    is_sample: bool
    score: int
    input_file_uuid: Optional[UUID]
    output_file_uuid: Optional[UUID]
    time_limit: int
    memory_limit: int
    is_disabled: bool
    is_deleted: bool


@dataclass
class S3File:
    uuid: UUID
    bucket: str
    key: str
    filename: str


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
    submit_time: datetime


@dataclass
class Judgment:
    id: int
    submission_id: int
    status: enum.JudgmentStatusType
    total_time: int
    max_memory: int
    score: int
    judge_time: datetime


@dataclass
class JudgeCase:
    judgment_id: int
    testcase_id: int
    status: enum.JudgmentStatusType
    time_lapse: int
    peak_memory: int
    score: int


@dataclass
class Essay:
    id: int
    challenge_id: int
    challenge_label: int
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
    submit_time: datetime


@dataclass
class AssistingData:
    id: int
    problem_id: int
    s3_file_uuid: UUID
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
    start_time: datetime
    end_time: datetime
    is_deleted: bool


@dataclass
class PeerReviewRecord:
    id: int
    peer_review_id: int
    grader_id: int
    receiver_id: int
    score: Optional[int]
    comment: Optional[str]
    submit_time: Optional[datetime]


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
