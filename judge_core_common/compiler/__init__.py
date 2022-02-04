import abc
import typing

from .. import base


class CompilerABC(abc.ABC):
    @abc.abstractmethod
    def compile(self,
                source_file: str, target_file: str,
                compile_args_compiler: typing.Callable[[str, str], typing.Sequence[str]]) \
            -> typing.Optional[base.VerdictType]:
        pass
