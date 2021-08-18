import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Sequence, Tuple

import pydantic
import pydantic.datetime_parse

import base.popo
from base.enum import FilterOperator
import exceptions as exc


def _ellipsis():
    return ellipsis


can_omit = pydantic.Field(default_factory=_ellipsis)


@dataclass
class AddOutput:
    id: int


@dataclass
class BrowseOutputBase:
    data: Any
    total_count: int


class Limit(pydantic.types.ConstrainedInt):
    gt = -1
    lt = 101


class Offset(pydantic.types.ConstrainedInt):
    gt = -1


FilterStr = Optional[pydantic.Json]
SorterStr = Optional[pydantic.Json]


def parse_filter(json_obj: FilterStr, column_types: Dict[str, type]) -> Sequence[base.popo.Filter]:
    filters: List[base.popo.Filter] = pydantic.parse_obj_as(List[base.popo.Filter], json_obj or [])

    for i, filter_ in enumerate(filters):
        try:
            to_parse_type = column_types[filter_.col_name]
        except KeyError:
            raise exc.IllegalInput

        if filter_.op in (FilterOperator.in_, FilterOperator.not_in):
            to_parse_type = set[to_parse_type]
        if filter_.op in (FilterOperator.between, FilterOperator.not_between):
            to_parse_type = Tuple[to_parse_type, to_parse_type]
        if filter_.op in (FilterOperator.like, FilterOperator.not_like):
            to_parse_type = str

        # filter_.val = pydantic.parse_obj_as(to_parse_type, filter_.val)
        filters[i] = base.popo.Filter(col_name=filter_.col_name, op=filter_.op,
                                      value=pydantic.parse_obj_as(to_parse_type, filter_.value))

    return filters


def parse_sorter(json_obj: FilterStr, column_types: Dict[str, type]) -> Sequence[base.popo.Sorter]:
    sorters: List[base.popo.Sorter] = pydantic.parse_obj_as(List[base.popo.Sorter], json_obj or [])

    if any(sorter.col_name not in column_types for sorter in sorters):
        raise exc.IllegalInput

    return sorters


class ServerTZDatetime(datetime.datetime):
    """
    A pydantic-compatible custom class to convert incoming datetime to server timezone datetime (without tzinfo)
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        converted = pydantic.datetime_parse.parse_datetime(value)

        if converted.tzinfo is not None:
            # Convert to server time
            converted = converted.astimezone().replace(tzinfo=None)

        return converted
