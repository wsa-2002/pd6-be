"""
Value Objects
"""
from dataclasses import dataclass
from typing import Optional

from base import enum


@dataclass
class AccountWithStudentCard:
    id: int
    student_id: str
    real_name: str
    username: str
    nickname: str
    alternative_email: Optional[str]
