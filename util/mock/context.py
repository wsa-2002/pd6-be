import inspect
from unittest.mock import patch

import util.context


class _Context(util.context.Context):
    _context = dict()

    def __enter__(self):
        print(inspect.currentframe().f_back.f_globals)
        self._patched = patch(f'{inspect.currentframe().f_back.f_globals["__package__"]}.context', self)
        self._patched.__enter__()
        return self


class Context:
    def __init__(self, module_name):
        if '.' not in module_name:
            module_name = inspect.currentframe().f_back.f_globals['__package__'] + '.' + module_name
        self._module_name = module_name
        self._context = _Context()

    def __enter__(self):
        self._patched = patch(f'{self._module_name}.context', self._context)
        self._patched.__enter__()
        return self._context

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._context._context = dict()
        return self._patched.__exit__(exc_type, exc_val, exc_tb)
