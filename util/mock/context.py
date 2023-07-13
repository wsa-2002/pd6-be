import types
from unittest.mock import patch

import util.context


class _Context(util.context.Context):
    _context = dict()

    def reset(self):
        self._context = dict()


class ContextInModule:
    def __init__(self, module: str | types.ModuleType, module_context_name='context'):
        if isinstance(module, str):
            self._mock_name = module + '.' + module_context_name
        elif isinstance(module, types.ModuleType):
            self._mock_name = module.__name__ + '.' + module_context_name
        else:
            raise AssertionError('Given module is not module nor string')

        self._context = _Context()

    def __enter__(self) -> _Context:
        self._patched = patch(self._mock_name, self._context)
        self._patched.__enter__()
        return self._context

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context.reset()
        return self._patched.__exit__(exc_type, exc_val, exc_tb)
