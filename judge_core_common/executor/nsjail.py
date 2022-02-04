import pathlib
import subprocess
import typing

from .. import base, do, log
from . import ExecutorABC, FileOutputExecutorABC


class NSJailExecutor(ExecutorABC):
    def __init__(self, work_dir: str):
        self.work_dir = work_dir

        pathlib.Path('/sys/fs/cgroup/memory/NSJAIL').mkdir(parents=True, exist_ok=True)
        pathlib.Path('/sys/fs/cgroup/cpu/NSJAIL').mkdir(parents=True, exist_ok=True)
        pathlib.Path('/sys/fs/cgroup/pids/NSJAIL').mkdir(parents=True, exist_ok=True)

    def execute(
            self,
            exec_args: typing.Sequence[str], stdin: bytes,
            memory_limit: base.KiloBytes, time_limit: base.MilliSeconds,
            dependencies: typing.Dict[str, str],  # outside: inside
    ) -> typing.Tuple[do.ExecuteResult, typing.Optional[base.VerdictType]]:
        log.info('Preparing to execute with nsjail...')

        log_file = pathlib.Path(self.work_dir, 'nsjail.log')
        log_file.touch()
        log_file.write_bytes(b'')

        usage_file = pathlib.Path(self.work_dir, 'nsjail.usage')
        usage_file.touch()
        usage_file.write_bytes(b'')

        nsjail_args = [
            'nsjail',
            '-Mo',
            '--user', '99999',
            '--group', '99999',
            '--chroot', '/',
            '--log', log_file,
            '--usage', usage_file,
            '--cgroup_pids_max', '64',
            '--cgroup_cpu_ms_per_sec', '1000',
            '--cgroup_mem_max', str(memory_limit * 1024),  # kilo-bytes to bytes
            '--max_cpus', '1',  # fixme: only single cpu for now
            '--time_limit', str(time_limit // 1000 + 1 + 1),  # ms -> seconds + int div buffer + nsjail buffer
        ]

        for dependency, inside_path in dependencies.items():
            nsjail_args += ['-R', f'{dependency}:{inside_path}']

        nsjail_args.append('--')
        nsjail_args += exec_args

        exec_result = subprocess.run(
            nsjail_args,
            input=stdin,
            capture_output=True,
        )

        log.info('Executing with nsjail done, produce logs')
        with open(log_file, 'rb') as f:
            nsjail_log = f.read()
        for line_log in nsjail_log.decode(errors='replace').split('\n'):
            log.info(line_log)

        with open(usage_file, 'r') as f:
            usage_data = f.readlines()
            log.info(usage_data)
            user_str, kernel_str, pass_str, memory_str, exit_code_str, exit_signal_str = usage_data
        time_lapse = int(user_str.split()[-1])  # ms
        peak_memory = int(memory_str.split()[-1])  # kilo-bytes
        exit_code = int(exit_code_str.split()[-1])
        exit_signal = int(exit_signal_str.split()[-1])

        return do.ExecuteResult(
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
            exit_code=exit_code,
            exit_signal=exit_signal,
            time_lapse=time_lapse,
            peak_memory=peak_memory,
        ), None


class FileOutputNSJailExecutor(FileOutputExecutorABC, NSJailExecutor):
    def __init__(self, work_dir: str):
        super().__init__(work_dir=work_dir)
        self.output_filename = ''

    def set_output_filename(self, output_filename: str):
        self.output_filename = output_filename

    def execute(
            self,
            exec_args: typing.Sequence[str], stdin: bytes,
            memory_limit: base.KiloBytes, time_limit: base.MilliSeconds,
            dependencies: typing.Dict[str, str],  # outside: inside
    ) -> typing.Tuple[do.ExecuteResult, typing.Optional[base.VerdictType]]:
        if not self.output_filename:
            raise ValueError("Output filename is not given")

        output_file = pathlib.Path(self.work_dir, self.output_filename)
        output_file.touch()
        output_file.write_bytes(b'')

        result, verdict = super().execute(exec_args=exec_args, stdin=stdin,
                                          memory_limit=memory_limit, time_limit=time_limit,
                                          dependencies=dependencies)

        with open(output_file, 'rb') as f:
            result.stdout = f.read()

        return result, verdict
