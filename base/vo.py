"""
Value Objects
"""
from dataclasses import dataclass

from base import enum


@dataclass
class BrowseClassMemberOutput:
    id: int
    username: str
    student_id: str
    real_name: str
    institute: str
    role: enum.RoleType
