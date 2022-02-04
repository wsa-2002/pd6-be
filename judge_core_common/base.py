import typing

from .cls import OrderedMixin, StrEnum


class VerdictType(OrderedMixin, StrEnum):
    accepted = 'ACCEPTED'
    wrong_answer = 'WRONG ANSWER'
    memory_limit_exceed = 'MEMORY LIMIT EXCEED'
    time_limit_exceed = 'TIME LIMIT EXCEED'
    runtime_error = 'RUNTIME ERROR'
    compile_error = 'COMPILE ERROR'
    contact_manager = 'CONTACT MANAGER'
    forbidden_action = 'FORBIDDEN ACTION'
    system_error = 'SYSTEM ERROR'


KiloBytes = typing.TypeVar('KiloBytes', bound=int)
MilliSeconds = typing.TypeVar('MilliSeconds', bound=int)
