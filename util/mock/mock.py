import contextlib
from copy import deepcopy
import typing
from unittest.mock import patch, Mock, AsyncMock


class CallRecord(typing.NamedTuple):
    mocked: Mock
    called_args: tuple[typing.Any]
    called_kwargs: dict[str, typing.Any]
    side_effect: typing.Any

    def __str__(self):
        f_args = ', '.join(str(arg) for arg in self.called_args)
        f_kwargs = ', '.join(f'{k}={v}' for k, v in self.called_kwargs.items())
        formatted = f_args + ', ' + f_kwargs if f_args and f_kwargs else f_args + f_kwargs

        return f'{self.__class__.__name__}: {self.mocked._extract_mock_name()}({formatted}) -> {self.side_effect}'


class CallRecorder:
    def __init__(self, module: 'MockModule', record_without_side_effect: CallRecord):
        self._module = module
        self._partial_record = record_without_side_effect
        self._called = False

    def _record(self, side_effect):
        if self._called:
            raise AssertionError('can only set call record once')

        self._module._register_call(CallRecord(
            self._partial_record.mocked,
            self._partial_record.called_args,
            self._partial_record.called_kwargs,
            side_effect,
        ))

        self._called = True

    def returns(self, *return_values):
        if len(return_values) > 1:
            return_values = (return_values,)
        self._record(return_values)

    def raises(self, exception: typing.Type[Exception] | Exception):
        self._record(exception)

    def executes(self, func):
        self._record(func)


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

    def call_with(self, *args, **kwargs) -> CallRecorder:
        copy_args = deepcopy(args)
        copy_kwargs = deepcopy(kwargs)
        return CallRecorder(self._module, CallRecord(self._mock, copy_args, copy_kwargs, None))

    def _prepare_mock_call(self) -> typing.ContextManager:
        @contextlib.contextmanager
        def manager():
            try:
                call_record = self._module._pop_call()
            except IndexError:
                raise AssertionError(f'Mocked {self} is not expected to be called')

            if call_record.mocked is not self._mock:
                raise AssertionError(f'Mocked {self} is not expected to be called; expected {call_record}')
            self._mock.side_effect = call_record.side_effect

            try:
                yield None
            finally:
                self._assert_mock_call(*call_record.called_args, **call_record.called_kwargs)

        return manager()

    def _assert_mock_call(self, *args, **kwargs):
        self._mock.assert_called_with(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        with self._prepare_mock_call():
            return self._mock(*args, **kwargs)


class MockAsyncFunction(MockFunction):
    MockType = AsyncMock

    def _assert_mock_call(self, *args, **kwargs):
        self._mock.assert_awaited_with(*args, **kwargs)

    async def __call__(self, *args, **kwargs):
        with self._prepare_mock_call():
            return await self._mock(*args, **kwargs)


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
        self._global_module = MockModule(self, '')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for unpatch_func in self._unpatch_funcs:
            unpatch_func(exc_type, exc_val, exc_tb)

        if self._calls:
            raise AssertionError(f'{len(self._calls)} expected call(s) not fulfilled, next one is {self._calls[0]}')

    def _patch(self, name, mocked):
        patched = patch(name, mocked)
        patched.__enter__()
        self._unpatch_funcs.append(patched.__exit__)

    def mock_module(self, module_name: str) -> MockModule:
        module = MockModule(self, module_name)
        self._patch(module_name, module)
        return module

    def mock_global_class(self, class_name: str, new_class: typing.Type):
        def _new(*args, **kwargs):
            _, args = args[0], args[1:]  # first item is the original class itself
            return new_class(*args, **kwargs)

        self._patch(f'{class_name}.__new__', _new)

    def mock_global_func(self, func_name: str) -> MockFunction:
        mocked = self._global_module.func(func_name)
        self._patch(func_name, mocked)
        return mocked

    def mock_global_async_func(self, func_name: str) -> MockAsyncFunction:
        mocked = self._global_module.async_func(func_name)
        self._patch(func_name, mocked)
        return mocked

    def _register_call(self, record: CallRecord):
        self._calls.append(record)

    def _pop_call(self) -> CallRecord:
        return self._calls.pop(0)
