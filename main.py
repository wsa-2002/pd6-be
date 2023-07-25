# Setup loggers from yaml


with open('logging.yaml', 'r') as conf:
    import yaml
    log_config = yaml.safe_load(conf.read())

    import logging.config
    logging.config.dictConfig(log_config)


import log


# Create the FastAPI application

from config import app_config
from middleware.api import FastAPI
from util import api_doc
from version import version

app = FastAPI(
    title=app_config.title,
    version=version,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    description=f"""
<h2>Documentation</h2>
{api_doc.all_docs()}
""".strip(),
)


# Hook startup and shutdown services for application
# Cyclic import should be avoided!


@app.on_event('startup')
async def app_startup():
    log.info('Database initializing...')
    from config import db_config
    from persistence.database import pool_handler
    await pool_handler.initialize(db_config=db_config)
    log.info('Database initialized')

    log.info('SMTP initializing...')
    from config import smtp_config
    from persistence.email import smtp_handler
    await smtp_handler.initialize(smtp_config=smtp_config)
    log.info('SMTP initialized')

    log.info('S3 initializing...')
    from config import s3_config
    from persistence.s3 import s3_handler
    await s3_handler.initialize(s3_config=s3_config)
    log.info('S3 initialized')

    log.info('AMQP initializing...')
    from config import amqp_config

    log.info('AMQP Publisher initializing...')
    from persistence.amqp_publisher import amqp_publish_handler
    await amqp_publish_handler.initialize(amqp_config=amqp_config)
    log.info('AMQP Publisher initialized')

    log.info('AMQP Consumer initializing...')
    from persistence.amqp_consumer import make_consumer
    import processor.amqp
    report_consumer = make_consumer(amqp_config=amqp_config,
                                    queue_name=amqp_config.report_queue_name,
                                    consume_function=processor.amqp.save_report)
    import asyncio
    asyncio.ensure_future(report_consumer(asyncio.get_event_loop()))
    log.info('AMQP Consumer initialized')


@app.on_event('shutdown')
async def app_shutdown():
    from persistence.database import pool_handler
    await pool_handler.close()

    from persistence.email import smtp_handler
    await smtp_handler.close()

    from persistence.s3 import s3_handler
    await s3_handler.close()

    from persistence.amqp_publisher import amqp_publish_handler
    await amqp_publish_handler.close()


# Add middlewares
# Order matters! First added middlewares are executed last.

import middleware.db_access_log
app.middleware('http')(middleware.db_access_log.middleware)

import middleware.auth
app.middleware('http')(middleware.auth.middleware)

import middleware.logging
app.middleware('http')(middleware.logging.middleware)

from config import profiler_config
if profiler_config.enabled:
    import middleware.profiler
    app.middleware('http')(middleware.profiler.middleware)

import middleware.tracker
app.middleware('http')(middleware.tracker.middleware)

import starlette_context.middleware
app.add_middleware(starlette_context.middleware.RawContextMiddleware)


# Add global exception handler

import middleware.envelope
middleware.envelope.hook_exception_envelope_handler(app)


# Register routers
import processor.http_api

processor.http_api.register_routers(app)


# Instrument for prometheus
from prometheus_fastapi_instrumentator import Instrumentator, metrics as pfi_metrics

instrumentator = Instrumentator().add(pfi_metrics.default(latency_lowr_buckets=(
    0.010,
    0.025,
    0.050,
    0.075,
    0.100,
    0.250,
    0.500,
    0.750,
    1,
    2,
    3,
    4,
    5,
))).instrument(app).expose(app)
