# Create the FastAPI application

from config import app_config
from middleware import api

app = api.FastAPI(
    title=app_config.title,
    docs_url=app_config.docs_url,
    redoc_url=app_config.redoc_url,
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
from middleware import auth
app.add_middleware(auth.Middleware)


# Register custom exception handlers
from fastapi.exceptions import RequestValidationError, HTTPException
from middleware import envelope
from exceptions import PdogsException
app.add_exception_handler(RequestValidationError, envelope.exception_handler)
app.add_exception_handler(HTTPException, envelope.exception_handler)
app.add_exception_handler(PdogsException, envelope.exception_handler)
app.add_exception_handler(Exception, envelope.exception_handler)  # General fallback


# Register routers
from api import register_routers
register_routers(app)
