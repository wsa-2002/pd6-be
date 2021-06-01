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
class Testdata:
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
