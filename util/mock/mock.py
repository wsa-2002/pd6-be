import typing
from unittest.mock import patch, Mock, AsyncMock


class CallRecord(typing.NamedTuple):
    mocked: Mock
    called_args: tuple[typing.Any]
    called_kwargs: dict[str, typing.Any]

    def __str__(self):
        f_args = ', '.join(str(arg) for arg in self.called_args)
        f_kwargs = ', '.join(f'{k}={v}' for k, v in self.called_kwargs.items())
        formatted = f_args + ', ' + f_kwargs if f_args and f_kwargs else f_args + f_kwargs

        return f'{self.__class__.__name__}: {self.mocked._extract_mock_name()}({formatted})'


class CallRecorder:
    def __init__(self, mocked: Mock):
        self._mock = mocked
        self._called = False

    def _record(self, side_effect):
        if self._called:
            raise AssertionError('can only set call record once')
        orig_side_effect = list(self._mock.side_effect)
        orig_side_effect.append(side_effect)
        self._mock.side_effect = orig_side_effect
        self._called = True

    def returns(self, *return_values):
        self._record(return_values)

    def raises(self, exception: typing.Type[Exception]):
        self._record(exception)


class MockFunction:
    MockType = Mock

    def __init__(self, module: 'MockModule', name: str):
        self._name = name
        self._module = module
        self._mock = self.MockType(side_effect=list(), name=f'mocked {self}')

    def __str__(self):
        return f'{self._module}.{self._name}'

    def __repr__(self):
        return f'<{self.__class__.__name__} {self}>'

    def expect_call(self, *args, **kwargs) -> CallRecorder:
        self._module._register_call(CallRecord(self._mock, args, kwargs))
        return CallRecorder(self._mock)

    def __call__(self, *args, **kwargs):
        call_record = self._module._pop_call()
        if call_record.mocked is not self._mock:
            raise AssertionError(f'Mocked {self} is not expected to be called with: {args=} {kwargs=}')

        result = self._mock(*args, **kwargs)

        self._mock.assert_called_with(*call_record.called_args, **call_record.called_kwargs)

        return result


class MockAsyncFunction(MockFunction):
    MockType = AsyncMock

    async def __call__(self, *args, **kwargs):
        call_record = self._module._pop_call()
        if call_record.mocked is not self._mock:
            raise AssertionError(f'Mocked {self} is not expected to be called with: {args=} {kwargs=}')

        result = await self._mock(*args, **kwargs)

        self._mock.assert_awaited_with(*call_record.called_args, **call_record.called_kwargs)

        return result


class MockModule:
    def __init__(self, controller: 'Controller', name: str):
        self._controller = controller
        self._mocked_funcs: dict[str, MockFunction | MockAsyncFunction] = dict()
        self._name = name

    def __str__(self):
        return f'{self._name}'

    def __repr__(self):
        return f'<MockModule {self}>'

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            pass

        try:
            return self._mocked_funcs[item]
        except KeyError:
            pass

        raise AssertionError(f'Unexpected function call {item} to mocked module {self}')

    def func(self, func_name: str) -> MockFunction:
        if func_name in self._mocked_funcs:
            mocked_func = self._mocked_funcs[func_name]
        else:
            mocked_func = MockFunction(self, func_name)
            self._mocked_funcs[func_name] = mocked_func

        if not isinstance(mocked_func, MockFunction):
            raise AssertionError(f'{self} should be a mock function')

        return mocked_func

    def async_func(self, func_name: str) -> MockAsyncFunction:
        if func_name in self._mocked_funcs:
            mocked_func = self._mocked_funcs[func_name]
        else:
            mocked_func = MockAsyncFunction(self, func_name)
            self._mocked_funcs[func_name] = mocked_func

        if not isinstance(mocked_func, MockAsyncFunction):
            raise AssertionError(f'{self} should be an async mock function')

        return mocked_func

    def _register_call(self, record: CallRecord):
        self._controller._register_call(record)

    def _pop_call(self) -> CallRecord:
        return self._controller._pop_call()


class Controller:
    def __init__(self):
        self._calls: list[CallRecord] = list()
        self._unpatch_funcs: list[typing.Callable] = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for unpatch_func in self._unpatch_funcs:
            unpatch_func(exc_type, exc_val, exc_tb)

        if self._calls:
            raise AssertionError(f'{len(self._calls)} expected call(s) not fulfilled, next one is {self._calls[0]}')

    def mock_module(self, module_name: str) -> MockModule:
        module = MockModule(self, module_name)

        patched = patch(module_name, module)
        patched.__enter__()
        self._unpatch_funcs.append(patched.__exit__)

        return module

    def _register_call(self, record: CallRecord):
        self._calls.append(record)

    def _pop_call(self) -> CallRecord:
        return self._calls.pop(0)
