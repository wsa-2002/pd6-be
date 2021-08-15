from dataclasses import dataclass
import typing

import pydantic

import base.popo
from base.enum import FilterOperator


def _ellipsis():
    return ellipsis


can_omit = pydantic.Field(default_factory=_ellipsis)


@dataclass
class AddOutput:
    id: int


@dataclass
class BrowseOutputBase:
    data: typing.Any
    total_count: int


FilterStr = typing.Optional[pydantic.Json]


def parse_filter(json_obj: FilterStr, value_type=None) -> typing.Sequence[base.popo.Filter]:
    parsed: typing.Sequence[base.popo.Filter] = pydantic.parse_obj_as(typing.Sequence[base.popo.Filter], json_obj or [])

    if value_type:
        for filter_ in parsed:
            to_parse_type = value_type
            if filter_.op in (FilterOperator.in_, FilterOperator.not_in):
                to_parse_type = set[to_parse_type]
            if filter_.op in (FilterOperator.between, FilterOperator.not_between):
                to_parse_type = tuple[to_parse_type, to_parse_type]
            if filter_.op in (FilterOperator.like, FilterOperator.not_like):
                to_parse_type = str

            filter_.val = pydantic.parse_obj_as(to_parse_type, filter_.val, )

    return parsed
