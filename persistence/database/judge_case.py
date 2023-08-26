from typing import Iterable

from base import do, enum
from .base import FetchAll


async def batch_get_with_judgment(testcase_id: int, judgment_ids: Iterable[int], verdict: enum.VerdictType = None) -> \
        dict[int, do.JudgeCase]:
    cond_sql = ', '.join(str(judgment_id) for judgment_id in judgment_ids)
    async with FetchAll(
            event='batch get judge case with judgment ids',
            sql=fr'SELECT judge_case.judgment_id, judge_case.testcase_id, judge_case.verdict, '
                fr'       judge_case.time_lapse, judge_case.peak_memory, judge_case.score '
                fr'  FROM judge_case'
                fr' INNER JOIN testcase'
                fr'         ON testcase.id = judge_case.testcase_id'
                fr'      WHERE judge_case.testcase_id = %(testcase_id)s'
                fr'{f"     AND judge_case.judgment_id IN ({cond_sql})" if cond_sql else ""}'
                fr'{"     AND judge_case.verdict = %(verdict)s" if verdict else ""}',
            testcase_id=testcase_id, verdict=verdict,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return {judgment_id: do.JudgeCase(judgment_id=judgment_id, testcase_id=testcase_id, verdict=verdict,
                                          time_lapse=time_lapse, peak_memory=peak_memory, score=score)
                for (judgment_id, testcase_id, verdict, time_lapse, peak_memory, score)
                in records}
