"""
Data Objects
"""
from dataclasses import dataclass
from typing import Optional

from base import enum
from base.cls import DataclassBase


@dataclass  # for PyCharm
class Account(DataclassBase):
    id: int
    name: str
    nickname: str
    real_name: str
    role: enum.RoleType
    is_enabled: bool
    alternative_email: Optional[str] = None


@dataclass  # for PyCharm
class Institute(DataclassBase):
    id: int
    name: str
    email_domain: str
    is_enabled: bool


@dataclass  # for PyCharm
class StudentCard(DataclassBase):
    id: int
    institute_id: int
    department: str
    student_id: str
    email: str
    is_enabled: bool


@dataclass  # for PyCharm
class Course(DataclassBase):
    id: int
    name: str
    type: enum.CourseType
    is_enabled: bool
    is_hidden: bool

@dataclass # for PyCharm
class Team(DataclassBase):
    id: int
    name: str
    class_id: int
    is_enabled: bool
    is_hidden: bool