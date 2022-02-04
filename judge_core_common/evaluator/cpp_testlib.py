import os
import pathlib
import shutil
import typing

from .. import base, const
from ..compiler import CompilerABC
from ..executor import FileOutputExecutorABC
from . import EvaluatorABC


class CppTestlibEvaluator(EvaluatorABC):
    def __init__(self, work_dir: str, code_file: str, compiler: CompilerABC, executor: FileOutputExecutorABC):
        self.work_dir = work_dir

        # compile
        shutil.copy(os.path.join(pathlib.Path(__file__).resolve().parent, 'testlib.h'),
                    os.path.join(pathlib.Path(code_file).resolve().parent, 'testlib.h'))  # put the testlib.h into place
        source_file = os.path.join(work_dir, 'testlib_source.cpp')
        shutil.copy(code_file, source_file)
        self.executable = os.path.join(work_dir, 'testlib_compiled')
        testlib_h = os.path.join(work_dir, 'testlib.h')
        shutil.copy(os.path.join(pathlib.Path(code_file).resolve().parent, 'testlib.h'), testlib_h)
        self.compile_verdict = compiler.compile(
            code_file, self.executable,
            lambda code, compiled: ['g++', code, '-O2', '-std=c++11', '-w', '-static', '-o', compiled])

        self.executor = executor

    def grade(self, testcase_score: int, testcase_input: bytes, testcase_output: bytes, actual_output: bytes) -> \
            typing.Tuple[int, base.VerdictType]:
        if self.compile_verdict:
            return 0, self.compile_verdict

        input_txt = pathlib.Path(self.work_dir, 'cpp_testlib_input.txt')
        input_txt.touch()
        input_txt.write_bytes(testcase_input)
        output_txt = pathlib.Path(self.work_dir, 'cpp_testlib_output.txt')
        output_txt.touch()
        output_txt.write_bytes(actual_output)
        answer_txt = pathlib.Path(self.work_dir, 'cpp_testlib_answer.txt')
        answer_txt.touch()
        answer_txt.write_bytes(testcase_output)

        self.executor.set_output_filename(const.CUSTOMIZED_JUDGE_CPP_TESTLIB_SCORE_FILENAME)
        result, verdict = self.executor.execute(
            exec_args=[
                self.executable,
                input_txt.name,
                output_txt.name,
                answer_txt.name,
            ],
            stdin=b'',
            memory_limit=const.CUSTOMIZED_JUDGE_CPP_TESTLIB_MEMORY_LIMIT,
            time_limit=const.CUSTOMIZED_JUDGE_CPP_TESTLIB_TIME_LIMIT,
            dependencies={
                str(input_txt.resolve()): input_txt.name,
                str(output_txt.resolve()): output_txt.name,
                str(answer_txt.resolve()): answer_txt.name,
            },
        )

        if verdict:
            return 0, verdict

        if result.exit_code == 1:
            score = int(result.stdout)
            return score, base.VerdictType.accepted

        return 0, base.VerdictType.wrong_answer
