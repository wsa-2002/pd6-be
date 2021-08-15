from dataclasses import dataclass
from typing import Union, Any

from base import enum


@dataclass
class Filter:
    op: enum.FilterOperator
    val: Union[Any, set, tuple, str]  # normal, in, between, like
