import common.do
import common.const
from util import serialize

from . import amqp_publish_handler


async def send_judge(task: common.do.JudgeTask, language_queue_name: str, priority: int = common.const.PRIORITY_NONE):
    await amqp_publish_handler.publish(
        queue_name=language_queue_name,
        message=serialize.marshal(task).encode(),
        priority=priority,
    )
