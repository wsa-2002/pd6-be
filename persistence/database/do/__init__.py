"""
Data Objects
"""
from dataclasses import dataclass
from typing import Optional

from base.cls import DataclassBase
from base.enum import Role


@dataclass  # for PyCharm
class Account(DataclassBase):
    id: int
    name: str
    nickname: str
    real_name: str
    role: Role
    is_enabled: bool
    alternative_email: Optional[str] = None
