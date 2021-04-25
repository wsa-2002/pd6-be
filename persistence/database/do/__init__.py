"""
Data Objects
"""
from dataclasses import dataclass
from typing import Optional

from base.cls import DataclassBase
from base.enum import RoleType


@dataclass  # for PyCharm
class Account(DataclassBase):
    id: int
    name: str
    nickname: str
    real_name: str
    role: RoleType
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
