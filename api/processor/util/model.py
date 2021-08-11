import pydantic


def _ellipsis():
    return ellipsis


can_omit = pydantic.Field(default_factory=_ellipsis)
