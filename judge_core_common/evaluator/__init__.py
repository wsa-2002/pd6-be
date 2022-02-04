import abc
import typing

from .. import base


class EvaluatorABC(abc.ABC):
    @abc.abstractmethod
    def grade(self, testcase_score: int, testcase_input: bytes, testcase_output: bytes, actual_output: bytes) -> \
            typing.Tuple[int, base.VerdictType]:
        pass
