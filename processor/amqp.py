import service

from judge_core_common import marshal


async def save_report(body: bytes) -> None:
    report = marshal.unmarshal_report(body)
    await service.judgment.save_report(report)
