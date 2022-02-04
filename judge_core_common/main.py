import os
import typing

from . import base, config, const, do, log, downloader, compiler, executor, evaluator


class Judge:
    def __init__(
            self,
            work_dir: str,
            exec_args_compiler: typing.Callable[[str], typing.Sequence[str]],
            compile_args_compiler: typing.Callable[[str, str], typing.Sequence[str]],
            downloader_impl: downloader.DownloaderABC,
            compiler_impl: compiler.CompilerABC,
            executor_impl: executor.ExecutorABC,
            evaluator_impl: evaluator.EvaluatorABC,
    ):
        self.work_dir = work_dir
        self.exec_args_compiler = exec_args_compiler
        self.compile_args_compiler = compile_args_compiler
        self.downloader = downloader_impl
        self.compiler = compiler_impl
        self.executor = executor_impl
        self.evaluator = evaluator_impl

    def judge(self, task: do.JudgeTask) -> do.JudgeReport:
        log.info(f'Running judge task for submission id {task.submission.id}')

        report = do.JudgeReport(
            judgment=do.Judgment(
                submission_id=task.submission.id,
                verdict=base.VerdictType.system_error,
                total_time=0,
                max_memory=0,
                score=0,
            ),
            judge_cases=[],
        )

        # 1. download submission
        source_file, verdict = self.downloader.to_dir(task.submission.file_url,
                                                      directory=self.work_dir,
                                                      filename=f'source')
        if verdict:
            report.judgment.verdict = verdict
            return report

        # 2. compile
        compiled_file = os.path.join(self.work_dir, 'compiled')
        verdict = self.compiler.compile(source_file, compiled_file, self.compile_args_compiler)
        if verdict:
            report.judgment.verdict = verdict
            return report

        # 3. special case: no testcase
        if not task.testcases:
            report.judgment.verdict = base.VerdictType.contact_manager
            return report

        # 4. resolve cross-testcase dependencies
        assisting_data_dir = os.path.join(self.work_dir, 'assisting_data')
        os.mkdir(assisting_data_dir)
        _, verdict = self.downloader.batch_to_dir(
            urls=[ad.file_url for ad in task.assisting_data],
            directory=assisting_data_dir,
            filenames=[ad.filename for ad in task.assisting_data],
        )
        if verdict:
            report.judgment.verdict = verdict
            return report

        # 5. execute testcases
        for testcase in task.testcases:
            judge_case = do.JudgeCase(testcase_id=testcase.id, verdict=base.VerdictType.system_error,
                                      time_lapse=0, peak_memory=0, score=0)
            report.judge_cases += [judge_case]
            log.info(f'Get input data for {testcase.id=}')

            # 5a. execute

            if url := testcase.input_file_url:
                input_data, verdict = self.downloader.as_bytes(url)
                if verdict:
                    judge_case.verdict = verdict
                    continue
            else:
                input_data = b''

            execute_result, verdict = self.executor.execute(
                exec_args=self.exec_args_compiler(compiled_file),
                stdin=input_data,
                memory_limit=testcase.memory_limit,
                time_limit=testcase.time_limit,
                dependencies={
                    assisting_data_dir: const.ASSISTING_DATA_DIR,
                }
            )

            if config.JudgeConfig().log_io:
                log.info('--- actual stdout ---\n' + execute_result.stdout.decode(errors='replace'))
                log.info('--- actual stderr ---\n' + execute_result.stderr.decode(errors='replace'))
                log.info('--- logio end ---')

            # 5b. check basic cases

            judge_case.time_lapse = execute_result.time_lapse
            judge_case.peak_memory = execute_result.peak_memory

            if verdict:
                judge_case.verdict = verdict
                continue

            if execute_result.time_lapse > testcase.time_limit:
                log.info(f'TLE: {testcase.time_limit} < {execute_result.time_lapse}')
                judge_case.score, judge_case.verdict = 0, base.VerdictType.time_limit_exceed

            if execute_result.peak_memory > testcase.memory_limit:
                log.info(f'MLE: {testcase.memory_limit} < {execute_result.peak_memory}')
                judge_case.score, judge_case.verdict = 0, base.VerdictType.memory_limit_exceed

            if execute_result.stderr:
                log.info(f'RE: {execute_result.stderr}')
                judge_case.score, judge_case.verdict = 0, base.VerdictType.runtime_error

            # 5c. evaluate

            if url := testcase.output_file_url:
                output_data, verdict = self.downloader.as_bytes(url)
                if verdict:
                    judge_case.verdict = verdict
                    continue
            else:
                output_data = b''

            score, verdict = self.evaluator.grade(testcase.score, input_data, output_data, execute_result.stdout)
            judge_case.score = score
            judge_case.verdict = verdict

        # 6. aggregate
        report.judgment.verdict = max(judge_case.verdict for judge_case in report.judge_cases)
        report.judgment.total_time = sum(judge_case.time_lapse for judge_case in report.judge_cases)
        report.judgment.max_memory = max(judge_case.peak_memory for judge_case in report.judge_cases)
        report.judgment.score = sum(judge_case.score for judge_case in report.judge_cases)
        if task.problem.full_score is not None:
            report.judgment.score = min(task.problem.full_score, report.judgment.score)

        return report
