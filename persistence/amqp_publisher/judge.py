from judge_core_common import do as judge_do, marshal

from . import amqp_publish_handler


async def send_judge(task: judge_do.JudgeTask, language_queue_name: str):
    await amqp_publish_handler.publish(
        queue_name=language_queue_name,
        message=marshal.marshal(task),
    )
