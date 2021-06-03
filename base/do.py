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
    is_enabled: bool
    alternative_email: Optional[str] = None


@dataclass
class Institute:
    id: int
    name: str
    email_domain: str
    is_enabled: bool


@dataclass
class StudentCard:
    id: int
    institute_id: int
    department: str
    student_id: str
    email: str
    is_enabled: bool


@dataclass
class Course:
    id: int
    name: str
    type: enum.CourseType
    is_enabled: bool
    is_hidden: bool


@dataclass
class Class:
    id: int
    name: str
    course_id: int
    is_enabled: bool
    is_hidden: bool


@dataclass
class Team:
    id: int
    name: str
    class_id: int
    is_enabled: bool
    is_hidden: bool


@dataclass
class Member:
    member_id: int
    role: enum.RoleType


@dataclass
class Challenge:
    id: int
    class_id: int
    type: enum.ChallengeType
    name: str
    setter_id: int
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    is_enabled: bool
    is_hidden: bool


@dataclass
class Problem:
    id: int
    type: enum.ChallengeType
    name: str
    setter_id: int
    full_score: int
    description: Optional[str]
    source: Optional[str]
    hint: Optional[str]
    is_enabled: bool
    is_hidden: bool


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
    is_enabled: bool
    is_hidden: bool


@dataclass
class SubmissionLanguage:
    id: int
    name: str
    version: str


@dataclass
class Submission:
    id: int
    account_id: int
    problem_id: int
    challenge_id: Optional[int]
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
class Grade:
    id: int
    receiver_id: int
    grader_id: int
    class_id: int
    title: str
    score: Optional[int]
    comment: Optional[str]
    update_time: datetime


@dataclass
class PeerReview:
    id: int
    target_challenge_id: int
    target_problem_id: int
    setter_id: int
    description: str
    min_score: int
    max_score: int
    max_review_count: int
    start_time: datetime
    end_time: datetime
    is_enabled: bool
    is_hidden: bool


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
class Announcement:
    id: int
    title: str
    content: str
    author_id: int
    post_time: datetime
    expire_time: datetime
