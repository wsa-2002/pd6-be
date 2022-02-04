import typing

from .. import base, config, log
from . import EvaluatorABC


class StandardEvaluator(EvaluatorABC):
    def grade(self, testcase_score: int, testcase_input: bytes, testcase_output: bytes, actual_output: bytes) -> \
            typing.Tuple[int, base.VerdictType]:

        # try to check without decoding
        if testcase_output == actual_output:
            if config.JudgeConfig().log_io:
                log.info('logio skipped because output/expected is exactly the same :smile:')
            return testcase_score, base.VerdictType.accepted

        # check with decoding
        try:
            testcase_output_str = testcase_output.decode().rstrip(' \r\n')
        except UnicodeDecodeError:
            return 0, base.VerdictType.contact_manager
        actual_output_str = actual_output.decode(errors='replace').rstrip(' \r\n')

        if actual_output_str != testcase_output_str:
            return 0, base.VerdictType.wrong_answer

        return testcase_score, base.VerdictType.accepted
