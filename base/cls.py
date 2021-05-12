import dataclasses as _dc
import enum
from typing import TypeVar, Type, Dict


T = TypeVar("T")


class DataclassMeta(type):
    def __new__(mcs, typename, bases, ns, *,
                init=True, repr=True, eq=True, order=False, unsafe_hash=False, frozen=False):
        cls = super().__new__(mcs, typename, bases, ns)
        return _dc.dataclass(cls, init=init, repr=repr, eq=eq, order=order, unsafe_hash=unsafe_hash, frozen=frozen)


class DataclassBase(metaclass=DataclassMeta):
    """
    It's an inheritable `Dataclass`!

    `@dataclass()` parameters can be passed in like: `class MyDataclass(Dataclass, order=True)`

    If you don't want PyCharm to complain about not recognizing dataclass, just `@dataclass` again.

    Also hooks a `__post_init__`.
    """

    # def __post_init__(self):
    #     for field in _dc.fields(self):
    #         value = getattr(self, field.name)
    #         if not isinstance(value, field.type):
    #             try:
    #                 converted_value = field.type(value)
    #             except:
    #                 raise ValueError(f'Expected {field.name} to be {field.type}, '
    #                                  f'got non-convertible value {repr(value)}')
    #             else:
    #                 setattr(self, field.name, converted_value)

    def as_dict(self) -> Dict:
        return _dc.asdict(self)

    def as_resp_dict(self) -> Dict:
        """
        Escapes underscore to hyphen
        """
        return {k.replace('_', '-'): v for k, v in self.as_dict().items()}


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
