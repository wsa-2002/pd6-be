import typing
import unittest
from unittest.mock import patch, AsyncMock


class AsyncCallRecord(typing.NamedTuple):
    mocked: AsyncMock
    called_args: tuple[typing.Any]
    called_kwargs: dict[str, typing.Any]

    def __str__(self):
        f_args = ', '.join(self.called_args)
        f_kwargs = ', '.join(f'{k}={v}' for k, v in self.called_kwargs.items())
        formatted = f_args + ', ' + f_kwargs if f_args and f_kwargs else f_args + f_kwargs

        return f'AsyncCallRecord: {self.mocked._extract_mock_name()}({formatted})'


class OneTimeResultRecorder:
    def __init__(self, mocked: unittest.mock.Mock):
        self._mock = mocked
        self._called = False

    def _record(self, side_effect):
        if self._called:
            raise AssertionError('can only set once')
        orig_side_effect = list(self._mock.side_effect)
        orig_side_effect.append(side_effect)
        self._mock.side_effect = orig_side_effect
        self._called = True

    def returns(self, *return_values):
        self._record(*return_values)

    def raises(self, exception: typing.Type[Exception]):
        self._record(exception)


class AsyncMockFunction:
    def __init__(self, module: 'AsyncMockModule', name: str):
        self._name = name
        self._module = module
        self._mock = AsyncMock(side_effect=list(), name=f'mocked {self}')

    def expect_call(self, *args, **kwargs) -> OneTimeResultRecorder:
        self._module._register_call(AsyncCallRecord(self._mock, args, kwargs))
        return OneTimeResultRecorder(self._mock)

    def __str__(self):
        return f'{self._module}.{self._name}'

    def __repr__(self):
        return f'<AsyncMockFunction {self}>'

    async def __call__(self, *args, **kwargs):
        call_record = self._module._pop_call()
        if call_record.mocked is not self._mock:
            raise AssertionError(f'Mocked {self} is not expected to be called with: {args=} {kwargs=}')

        result = await self._mock(*args, **kwargs)

        self._mock.assert_awaited_with(*call_record.called_args, **call_record.called_kwargs)

        return result


class AsyncMockModule:
    def __init__(self, controller: 'AsyncMockController', name: str):
        self._controller = controller
        self._mocked_funcs: dict[str, typing.Any] = dict()
        self._name = name

    def __str__(self):
        return self._name

    def __repr__(self):
        return f'<AsyncMockModule {self}>'

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            pass

        try:
            return self._mocked_funcs[item]
        except KeyError:
            raise AssertionError(f'Unexpected function call {item} to mocked module {self}')

    def function(self, func_name: str) -> AsyncMockFunction:
        if func_name in self._mocked_funcs:
            mocked_func = self._mocked_funcs[func_name]
        else:
            mocked_func = AsyncMockFunction(self, func_name)
            self._mocked_funcs[func_name] = mocked_func

        return mocked_func

    def _register_call(self, record: AsyncCallRecord):
        self._controller._register_call(record)

    def _pop_call(self) -> AsyncCallRecord:
        return self._controller._pop_call()


class AsyncMockController:
    def __init__(self):
        self._calls: list[AsyncCallRecord] = list()
        self._patches = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patched in self._patches:
            patched.__exit__(exc_type, exc_val, exc_tb)

        if self._calls:
            raise AssertionError(f'{len(self._calls)} expected call(s) not fulfilled, next one is {self._calls[0]}')

    def mock_module(self, module_name: str) -> AsyncMockModule:
        module = AsyncMockModule(self, module_name)
        patched = patch(module_name, module)
        _mock = patched.__enter__()

        self._patches.append(patched)
        return module

    def _register_call(self, record: AsyncCallRecord):
        self._calls.append(record)

    def _pop_call(self) -> AsyncCallRecord:
        return self._calls.pop(0)
