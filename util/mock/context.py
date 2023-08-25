from unittest.mock import patch

import util.context


class _ContextDict(dict):
    @staticmethod
    def exists():
        return False


class Context:
    def __init__(self):
        self._patch = patch(f'{util.context.__name__}.{util.context.Context.__name__}._context', _ContextDict())

    def __enter__(self) -> util.context.Context:
        self._patch.__enter__()
        return util.context.context

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._patch.__exit__(exc_type, exc_val, exc_tb)
