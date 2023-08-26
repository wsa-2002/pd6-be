import datetime
from dataclasses import dataclass
import typing

import pydantic
import pydantic.datetime_parse

import base.popo
from base.enum import FilterOperator
import exceptions as exc

T = typing.TypeVar('T')


def _ellipsis():
    return Ellipsis


can_omit = pydantic.Field(default_factory=_ellipsis)


@dataclass
class AddOutput:
    id: int


@dataclass
class BrowseOutputBase:
    data: typing.Any
    total_count: int


class Limit(pydantic.types.ConstrainedInt):
    gt = -1
    lt = 101


class Offset(pydantic.types.ConstrainedInt):
    gt = -1


FilterStr = typing.Optional[pydantic.Json]
SorterStr = typing.Optional[pydantic.Json]


def parse_filter(json_obj: FilterStr, column_types: dict[str, type]) -> list[base.popo.Filter]:
    filters: list[base.popo.Filter] = pydantic.parse_obj_as(list[base.popo.Filter], json_obj or [])

    for i, filter_ in enumerate(filters):
        try:
            to_parse_type = column_types[filter_.col_name]
        except KeyError:
            raise exc.IllegalInput

        if filter_.op in (FilterOperator.in_, FilterOperator.not_in):
            to_parse_type = set[to_parse_type]
        if filter_.op in (FilterOperator.between, FilterOperator.not_between):
            to_parse_type = tuple[to_parse_type, to_parse_type]
        if filter_.op in (FilterOperator.like, FilterOperator.not_like):
            to_parse_type = str

        # filter_.val = pydantic.parse_obj_as(to_parse_type, filter_.val)
        converted = base.popo.Filter(col_name=filter_.col_name, op=filter_.op,
                                     value=pydantic.parse_obj_as(to_parse_type, filter_.value))

        if filter_.op in (FilterOperator.between, FilterOperator.not_between):
            if len(converted.value) != 2:
                raise exc.IllegalInput
        if filter_.op in (FilterOperator.like, FilterOperator.not_like):
            if column_types[converted.col_name] != str:
                raise exc.IllegalInput

        filters[i] = converted

    return filters


def parse_sorter(json_obj: FilterStr, column_types: dict[str, type]) -> list[base.popo.Sorter]:
    sorters: list[base.popo.Sorter] = pydantic.parse_obj_as(list[base.popo.Sorter], json_obj or [])

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


class CaseInsensitiveEmailStr(pydantic.EmailStr):
    @classmethod
    def validate(cls, value) -> str:
        validated = super().validate(value).lower()
        if '+' in validated:
            raise exc.account.InvalidEmail
        return validated


NonEmptyStr = pydantic.constr(min_length=1)
TrimmedNonEmptyStr = pydantic.constr(strip_whitespace=True, min_length=1)
