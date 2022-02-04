import abc
import typing

from .. import base, do


class ExecutorABC(abc.ABC):
    @abc.abstractmethod
    def execute(
            self,
            exec_args: typing.Sequence[str], stdin: bytes,
            memory_limit: base.KiloBytes, time_limit: base.MilliSeconds,
            dependencies: typing.Dict[str, str],  # outside: inside
    ) -> typing.Tuple[do.ExecuteResult, typing.Optional[base.VerdictType]]:
        pass


class FileOutputExecutorABC(ExecutorABC):
    @abc.abstractmethod
    def set_output_filename(self, output_filename: str):
        pass
