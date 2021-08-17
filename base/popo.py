from typing import Union, Any, NamedTuple

from base import enum


class Filter(NamedTuple):
    col_name: str
    op: enum.FilterOperator
    value: Union[Any, set, tuple, str]  # normal, in, between, like


class Sorter(NamedTuple):
    col_name: str
    order: enum.SortOrder
