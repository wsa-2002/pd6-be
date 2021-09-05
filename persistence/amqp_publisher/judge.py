from judge_core_common import do as judge_do, marshal, util

from . import amqp_publish_handler


async def send_judge(task: judge_do.JudgeTask, language_name: str, language_version: str):
    await amqp_publish_handler.publish(
        queue_name=util.lang_queue_name(language_name=language_name, language_version=language_version),
        message=marshal.marshal(task),
    )
