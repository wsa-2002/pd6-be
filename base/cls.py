import enum
import typing

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
