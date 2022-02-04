import pika

from . import const, mcs
from .config import AmqpConfig


class AmqpHandler(metaclass=mcs.Singleton):
    def __init__(self):
        self._connection: pika.BlockingConnection = None  # Need to be init/closed manually
        self._channel = None

    def initialize(self, amqp_config: AmqpConfig):
        self._connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=amqp_config.host,
            port=amqp_config.port,
            credentials=pika.PlainCredentials(
                username=amqp_config.username,
                password=amqp_config.password,
            ),
            heartbeat=120,
        ))

    def close(self):
        self._connection.close()

    def get_channel(self) -> pika.adapters.blocking_connection.BlockingChannel:
        if self._channel is None:
            self._channel = self._connection.channel()
        return self._channel


def make_channel(amqp_config: AmqpConfig, queue_name: str, callback):
    handler = AmqpHandler()

    channel = handler.get_channel()

    channel.queue_declare(queue=queue_name, durable=True, arguments={
        "x-max-priority": const.MAX_PRIORITY,
    })
    channel.queue_declare(queue=amqp_config.report_queue_name, durable=True)
    channel.basic_qos(prefetch_count=amqp_config.prefetch_count)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)

    return channel
