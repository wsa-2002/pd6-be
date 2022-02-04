import os
import shutil
import typing

from .. import base
from . import CompilerABC


class DummyCompiler(CompilerABC):
    def compile(self,
                source_file: str, target_file: str,
                compile_args_compiler: typing.Callable[[str, str], typing.Sequence[str]]) \
            -> typing.Optional[base.VerdictType]:
        shutil.copy(source_file, target_file)
        return None
