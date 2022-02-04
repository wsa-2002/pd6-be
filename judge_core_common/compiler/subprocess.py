import os
import subprocess
import typing

from .. import base, log
from . import CompilerABC


class SubprocessCompiler(CompilerABC):
    def compile(self,
                source_file: str, target_file: str,
                compile_args_compiler: typing.Callable[[str, str], typing.Sequence[str]]) \
            -> typing.Optional[base.VerdictType]:
        log.info('Compiling...')

        # Execute
        exec_result = subprocess.run(
            compile_args_compiler(source_file, target_file),
            capture_output=True,
            timeout=10,
        )

        if exec_result.stderr:
            log.info('Unable to compile, stderr:')
            log.info(exec_result.stderr.decode(errors='replace'))
            return base.VerdictType.compile_error

        log.info('Compiled, stdout:')
        log.info(exec_result.stdout.decode(errors='replace'))

        return None
