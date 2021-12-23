import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def _get_current_username_dependency(username: str, password: str):
    def dependency(credentials: HTTPBasicCredentials = Depends(security)):
        correct_username = secrets.compare_digest(credentials.username, username)
        correct_password = secrets.compare_digest(credentials.password, password)
        if not (correct_username and correct_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username
    return dependency


def _hook_swagger(app: FastAPI, url: str, openapi_url: str):
    @app.get(url, include_in_schema=False)
    async def handler():
        return get_swagger_ui_html(openapi_url=openapi_url, title="docs")


def _hook_redoc(app: FastAPI, url: str, openapi_url: str):
    @app.get(url, include_in_schema=False)
    async def handler():
        return get_redoc_html(openapi_url=openapi_url, title="docs")


def _hook_openapi(app: FastAPI, url: str):
    @app.get(url, include_in_schema=False)
    async def handler():
        return app.openapi()


def _hook_secret_swagger(app: FastAPI, url: str, openapi_url: str, username: str, password: str):
    @app.get(url, include_in_schema=False)
    async def handler(_=Depends(_get_current_username_dependency(username, password))):
        return get_swagger_ui_html(openapi_url=openapi_url, title="docs")


def _hook_secret_redoc(app: FastAPI, url: str, openapi_url: str, username: str, password: str):
    @app.get(url, include_in_schema=False)
    async def handler(_=Depends(_get_current_username_dependency(username, password))):
        return get_redoc_html(openapi_url=openapi_url, title="docs")


def _hook_secret_openapi(app: FastAPI, url: str, username: str, password: str):
    @app.get(url, include_in_schema=False)
    async def handler(_=Depends(_get_current_username_dependency(username, password))):
        return app.openapi()


def hook_docs(app: FastAPI):
    from config import app_config

    if not app_config.openapi_url:
        return

    username = app_config.docs_username
    password = app_config.docs_password
    use_secret = username and password

    openapi_url = app_config.openapi_url
    if use_secret:
        _hook_secret_openapi(app, url=openapi_url, username=username, password=password)
    else:
        _hook_openapi(app, url=openapi_url)

    if docs_url := app_config.docs_url:
        if use_secret:
            _hook_secret_swagger(app, url=docs_url, username=username, password=password, openapi_url=openapi_url)
        else:
            _hook_swagger(app, url=docs_url, openapi_url=openapi_url)

    if redoc_url := app_config.docs_url:
        if use_secret:
            _hook_secret_redoc(app, url=redoc_url, username=username, password=password, openapi_url=openapi_url)
        else:
            _hook_redoc(app, url=redoc_url, openapi_url=openapi_url)
