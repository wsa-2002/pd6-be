import os


class AmqpConfig:
    host = os.environ.get('AMQP_HOST')
    port = int(os.environ.get('AMQP_PORT'))
    username = os.environ.get('AMQP_USERNAME')
    password = os.environ.get('AMQP_PASSWORD')
    report_queue_name = os.environ.get('REPORT_QUEUE_NAME', 'report')
    prefetch_count = int(os.environ.get('AMQP_PREFETCH_COUNT', '1'))
    worker_count = int(os.environ.get('WORKER_COUNT', '1'))


class JudgeConfig:
    language_queue_name = os.environ.get('LANGUAGE_QUEUE_NAME')
    log_io = os.environ.get('LOG_IO', None)
