import typing


_P = typing.ParamSpec('_P')  # 一組參數
_T = typing.TypeVar('_T')  # 一個東西
_AsyncFunc = typing.Callable[_P, typing.Awaitable[_T]]


def unwrap(func: _AsyncFunc) -> _AsyncFunc:
    return func.__wrapped__
