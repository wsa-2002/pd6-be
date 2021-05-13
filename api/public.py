from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from middleware import envelope


router = APIRouter(tags=['Public'])


@router.get("/", status_code=418, response_class=HTMLResponse)
async def default_page():
    return r"""
<a href="/docs">/docs</a> or <a href="/redoc">/redoc</a>
<br>
<br>
<img src="https://i.imgur.com/dBUZ3Ig.png" alt="I am not PDOGS">
"""


@router.post('/account', tags=['Account-Control'], response_class=envelope.JSONResponse)
async def create_account():
    ...  # TODO


@router.post('/account/jwt', tags=['Account-Control'], response_class=envelope.JSONResponse)
async def login():
    return {'jwt': ...}  # TODO
