# Setup loggers from yaml


with open('logging.yaml', 'r') as conf:
    import yaml
    log_config = yaml.safe_load(conf.read())

    import logging.config
    logging.config.dictConfig(log_config)


# Create the FastAPI application

from config import app_config
from middleware import api
from util import api_doc

app = api.FastAPI(
    title=app_config.title,
    docs_url=app_config.docs_url,
    redoc_url=app_config.redoc_url,
    description=f"""{api_doc.to_collapsible(title='<h2>Documentation</h2>',
                                            content=api_doc.to_collapsible(title="**Error codes**",
                                                                           content=api_doc.gen_err_doc()))}""",
)


# Hook startup and shutdown services for application
# Cyclic import should be avoided!


@app.on_event('startup')
async def app_startup():
    from config import db_config
    from persistence.database import pool_handler
    await pool_handler.initialize(db_config=db_config)

    from config import smtp_config
    from persistence.email import smtp_handler
    await smtp_handler.initialize(smtp_config=smtp_config)


@app.on_event('shutdown')
async def app_shutdown():
    from persistence.database import pool_handler
    await pool_handler.close()

    from persistence.email import smtp_handler
    await smtp_handler.close()


# Add middlewares
# Order matters! First added middlewares are executed last.

import middleware.auth
app.add_middleware(middleware.auth.Middleware)

import middleware.logging
app.middleware('http')(middleware.logging.middleware)

import middleware.tracker
app.middleware('http')(middleware.tracker.middleware)

import starlette_context.middleware
app.add_middleware(starlette_context.middleware.RawContextMiddleware)


# Register routers
from api import register_routers
register_routers(app)
