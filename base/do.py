"""
Data Objects
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from base import enum


@dataclass
class Account:
    id: int
    name: str
    nickname: str
    real_name: str
    role: enum.RoleType
    is_deleted: bool
    alternative_email: Optional[str] = None


@dataclass
class Institute:
    id: int
    name: str
    email_domain: str
    is_disabled: bool


@dataclass
class StudentCard:
    id: int
    institute_id: int
    department: str
    student_id: str
    email: str
    is_deleted: bool


@dataclass
class Course:
    id: int
    name: str
    type: enum.CourseType
    is_hidden: bool
    is_deleted: bool


@dataclass
class Class:
    id: int
    name: str
    course_id: int
    is_hidden: bool
    is_deleted: bool


@dataclass
class Team:
    id: int
    name: str
    class_id: int
    is_hidden: bool
    is_deleted: bool


@dataclass
class Member:
    member_id: int
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
    is_hidden: bool
    is_deleted: bool


@dataclass
class Challenge:
    id: int
    class_id: int
    type: enum.ChallengeType
    title: str
    setter_id: int
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_hidden: bool
    is_deleted: bool


@dataclass
class Task:
    id: int
    challenge_id: int
    identifier: str
    selection_type: enum.TaskSelectionType
    problem_id: Optional[int]
    peer_review_id: Optional[int]
    is_hidden: bool
    is_deleted: bool


@dataclass
class Problem:
    id: int
    title: str
    setter_id: int
    full_score: int
    description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_hidden: bool
    is_deleted: bool


@dataclass
class Testcase:
    id: int
    problem_id: int
    is_sample: bool
    score: int
    input_file: str
    output_file: str
    time_limit: int
    memory_limit: int
    is_disabled: bool
    is_deleted: bool


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
    task_id: Optional[int]
    language_id: int
    content_file: str
    content_length: str
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
class PeerReview:
    id: int
    target_task_id: int
    setter_id: int
    description: str
    min_score: int
    max_score: int
    max_review_count: int
    start_time: datetime
    end_time: datetime
    is_hidden: bool
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
