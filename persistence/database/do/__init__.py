"""
Data Objects
"""
from dataclasses import dataclass
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
class Team:
    id: int
    name: str
    class_id: int
    is_enabled: bool
    is_hidden: bool
