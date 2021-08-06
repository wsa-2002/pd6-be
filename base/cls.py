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
        """
        Stolen from pydantic's datetime parser
        """
        if isinstance(value, pydantic.datetime_parse.datetime):
            return value

        if isinstance(value, bytes):
            value = value.decode()

        match = pydantic.datetime_parse.datetime_re.match(value)
        if match is None:
            raise pydantic.datetime_parse.errors.DateTimeError()

        kw = match.groupdict()
        if kw['microsecond']:
            kw['microsecond'] = kw['microsecond'].ljust(6, '0')

        tzinfo = pydantic.datetime_parse._parse_timezone(kw.pop('tzinfo'), pydantic.datetime_parse.errors.DateTimeError)
        kw_ = {k: int(v) for k, v in kw.items() if v is not None}
        kw_['tzinfo'] = tzinfo

        try:
            converted = pydantic.datetime_parse.datetime(**kw_)
        except ValueError:
            raise pydantic.datetime_parse.errors.DateTimeError()

        # Edited here: forces timezone to convert to utc
        if converted.tzinfo is not None:
            return converted.astimezone(tz=datetime.timezone.utc).replace(tzinfo=None)
        return converted
