"""
Value Objects
"""
from dataclasses import dataclass
from typing import Optional

from base import enum


@dataclass
class AccountWithDefaultStudentId:
    id: int
    student_id: str
    real_name: str
    username: str
    nickname: str
    alternative_email: Optional[str]


@dataclass
class MemberWithStudentCard:
    id: int
    username: str
    student_id: str
    real_name: str
    institute: str
    role: enum.RoleType
