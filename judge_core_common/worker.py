from . import amqp, config, log


class Worker:
    def __init__(self, worker_id, callback, amqp_config: config.AmqpConfig, judge_config: config.JudgeConfig):
        self.worker_id = worker_id
        self.callback = callback
        self.amqp_config = amqp_config
        self.judge_config = judge_config

    def run(self):
        log.set_worker(self.worker_id)
        log.info(f'Worker initializing...')

        amqp.AmqpHandler().initialize(config.AmqpConfig())

        log.info('AMQP initialized')

        channel = amqp.make_channel(amqp_config=self.amqp_config,
                                    queue_name=self.judge_config.language_queue_name,
                                    callback=self.callback)
        log.info(f'Worker start consuming')
        channel.start_consuming()
