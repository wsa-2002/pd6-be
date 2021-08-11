from dataclasses import dataclass

import pydantic


def _ellipsis():
    return ellipsis


can_omit = pydantic.Field(default_factory=_ellipsis)


@dataclass
class AddOutput:
    id: int


limit = 0
offset = 100


@dataclass
class BrowseOutputBase:
    total: int
    data: ...
