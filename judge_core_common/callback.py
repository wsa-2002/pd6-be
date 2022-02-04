import traceback

import typing

from . import amqp, config, do, log, marshal


def make_amqp_callback(amqp_config: config.AmqpConfig, executor: typing.Callable[[do.JudgeTask], do.JudgeReport]):
    def callback(channel, method, properties, body: bytes):
        try:
            log.info(f'Task received')
            task = marshal.unmarshal_task(body)
            log.set_task(task.submission.id)
            report = executor(task)
        except Exception as e:
            log.error(f'nack due to: {e}')
            log.error(traceback.format_exc())
            log.error(f'nack-ed body: {body.decode(errors="replace")}')
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        else:
            log.info(f'Task finished with verdict {report.judgment.verdict}')
            response = marshal.marshal(report)
            amqp.AmqpHandler().get_channel().basic_publish(exchange='',
                                                           routing_key=amqp_config.report_queue_name,
                                                           body=response)
            channel.basic_ack(delivery_tag=method.delivery_tag)
            log.info(f'Task acked')
        finally:
            log.set_task(None)

    return callback
