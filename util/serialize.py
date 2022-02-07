import dataclasses
from functools import partial
import json
import typing

import pydantic

T = typing.TypeVar('T')


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


dumps = partial(json.dumps, cls=JSONEncoder)
loads = partial(json.loads, cls=JSONEncoder)


def marshal(obj) -> str:
    return json.dumps(obj, cls=JSONEncoder)


def unmarshal(body: str | bytes, as_type: typing.Type[T]) -> T:
    return pydantic.parse_raw_as(as_type, body)
