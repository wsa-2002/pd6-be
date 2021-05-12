from fastapi import FastAPI

from config import app_config


app = FastAPI(
    title=app_config.title,
)


@app.on_event('startup')
async def app_startup():
    from config import db_config
    from persistence import database
    await database.initialize(db_config)


@app.on_event('shutdown')
async def app_shutdown():
    from persistence import database
    await database.close()


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
