import datetime
import enum
import typing

import pydantic.datetime_parse


T = typing.TypeVar("T")


class StrEnum(str, enum.Enum):
    """
    A class like enum.IntEnum -- a string version
    """
    pass


class OrderedMixin:
    """
    Mixin for Enum
    Order is retrieved by the definition-order of Enum values, with SMALLER VALUES FIRST!
    """

    def __gt__(self: T, other: T):
        items = tuple(self.__class__)
        return items.index(self).__gt__(items.index(other))

    def __lt__(self: T, other: T):
        return self != other and not self.__gt__(other)

    def __ge__(self: T, other: T):
        return self == other or self.__gt__(other)

    def __le__(self: T, other: T):
        return self == other or not self.__gt__(other)

    @property
    def smaller(self: T) -> T:
        items = tuple(self.__class__)
        self_index = items.index(self)
        return items[self_index-1] if self_index else items[0]

    @property
    def larger(self: T) -> T:
        items = tuple(reversed(self.__class__))
        self_index = items.index(self)
        return items[self_index-1] if self_index else items[0]


class NoTimezoneIsoDatetime(datetime.datetime):
    """
    A pydantic-compatible custom class to represent and validate ISO-format datetime without timezone info
    """
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        converted = pydantic.datetime_parse.parse_datetime(value)

        # forces timezone to be None
        if converted.tzinfo is not None:
            # Uses utc as default timezone
            converted = converted.astimezone(tz=datetime.timezone.utc).replace(tzinfo=None)

        return converted
