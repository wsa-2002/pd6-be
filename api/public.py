from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from middleware import envelope


router = APIRouter(tags=['Public'])


@router.get("/", status_code=418, response_class=HTMLResponse)
async def default_page():
    return r"""PDOGS-6 async
<br>
<a href="/docs">/docs</a> or <a href="/redoc">/redoc</a>"""


@router.post('/account', tags=['Account-Control'], response_class=envelope.JSONResponse)
async def create_account():
    ...  # TODO


@router.post('/account/jwt', tags=['Account-Control'], response_class=envelope.JSONResponse)
async def login():
    return {'jwt': ...}  # TODO
