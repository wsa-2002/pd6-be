import typing


_P = typing.ParamSpec('_P')
_T = typing.TypeVar('_T')
_AsyncFunc = typing.Callable[_P, typing.Awaitable[_T]]


def unwrap(func: _AsyncFunc) -> _AsyncFunc:
    return func.__wrapped__
