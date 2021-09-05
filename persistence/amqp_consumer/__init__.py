import asyncio
from typing import Callable, Coroutine, Any

import aio_pika

import log


def make_consumer(host: str, port: int, queue_name: str,
                  consume_function: Callable[[bytes], Coroutine[Any, Any, None]]) \
        -> Callable[[asyncio.events.AbstractEventLoop], Coroutine[Any, Any, None]]:
    async def main(loop: asyncio.events.AbstractEventLoop):
        log.info(f"Creating AMQP connection to {host=} {port=}")
        async with await aio_pika.connect(
            host=host,
            port=port,
            loop=loop,
        ) as connection:
            log.info(f'Created AMQP connection to {host=} {port=}, creating channel and queue {queue_name=}')

            channel: aio_pika.RobustChannel = await connection.channel()
            queue = await channel.declare_queue(
                queue_name,
                durable=True,
            )

            log.info(f"Created consuming queue, {queue_name=}")

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    message: aio_pika.IncomingMessage
                    log.info(f'Queue {queue_name} received message {message.message_id=} {len(message.body)=}')
                    try:
                        await consume_function(message.body)
                    except Exception as e:
                        log.exception(e)
                        await message.nack(requeue=False)
                        log.error(f'Message {message.message_id=} NACKed')
                        log.error(f'Message {message.message_id=} full body: {message.body.decode()}')
                    else:
                        await message.ack()
                        log.info(f'Message {message.message_id=} ACKed')

    return main
