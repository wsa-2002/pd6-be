"""
View Objects
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from base import enum


@dataclass
class ViewAccount:
    account_id: int
    username: str
    real_name: str
    student_id: Optional[str]


@dataclass
class ViewClassMember:
    account_id: int
    username: str
    student_id: Optional[str]
    real_name: str
    abbreviated_name: Optional[str]
    role: enum.RoleType
    class_id: int


@dataclass
class ViewAccessLog:
    account_id: Optional[int]
    username: Optional[str]
    student_id: Optional[str]
    real_name: Optional[str]
    ip: str
    resource_path: str
    request_method: str
    access_time: datetime
    access_log_id: int


@dataclass
class ViewSubmissionUnderClass:
    submission_id: int
    account_id: int
    username: str
    student_id: Optional[str]
    real_name: str
    challenge_id: int
    challenge_title: str
    problem_id: int
    challenge_label: str
    verdict: Optional[enum.VerdictType]
    submit_time: datetime
    class_id: int


@dataclass
class ViewMySubmission:
    submission_id: int
    course_id: Optional[int]
    course_name: Optional[str]
    class_id: Optional[int]
    class_name: Optional[str]
    challenge_id: Optional[int]
    challenge_title: Optional[str]
    problem_id: Optional[int]
    challenge_label: Optional[str]
    verdict: Optional[enum.VerdictType]
    submit_time: datetime
    account_id: int


@dataclass
class ViewMySubmissionUnderProblem:
    submission_id: int
    judgment_id: Optional[int]
    verdict: Optional[enum.VerdictType]
    score: Optional[int]
    total_time: Optional[int]
    max_memory: Optional[int]
    submit_time: datetime
    account_id: int
    problem_id: int


@dataclass
class ViewProblemSet:
    challenge_id: int
    challenge_title: str
    problem_id: int
    challenge_label: str
    problem_title: str
    class_id: int


@dataclass
class ViewGrade:
    account_id: int
    username: str
    student_id: Optional[str]
    real_name: str
    title: str
    score: Optional[str]
    update_time: datetime
    grade_id: int
    class_id: int


@dataclass
class ViewPeerReviewRecord:
    account_id: int
    username: str
    real_name: str
    student_id: Optional[str]
    peer_review_record_ids: Sequence[Optional[int]]
    peer_review_record_scores: Sequence[Optional[int]]
    average_score: Optional[float]
