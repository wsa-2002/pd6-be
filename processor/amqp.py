import service

from judge_core_common import marshal
import log


async def save_report(body: bytes) -> None:
    log.info('Received save report task')
    report = marshal.unmarshal_report(body)
    await service.judge.save_report(report)
