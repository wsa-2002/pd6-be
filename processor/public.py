from typing import Optional
from dataclasses import dataclass

from fastapi.responses import HTMLResponse
import pydantic
from pydantic import BaseModel

import exceptions as exc
from middleware import APIRouter, JSONResponse, enveloped
import service

from .util import model

router = APIRouter(tags=['Public'])


@router.get("/", status_code=418, response_class=HTMLResponse)
async def default_page():
    return await service.public.default_page()


# Warning: this location is statically used in email string
# Use "get" for convenience (access from browser)
@router.get('/email-verification', tags=['Account', 'Student Card'])
@router.post('/email-verification', tags=['Account', 'Student Card'])
@enveloped
async def email_verification(code: str):
    await service.account.verify_email(code=code)


class ForgetPasswordInput(BaseModel):
    username: str
    email: str


@router.post('/account/forget-password', tags=['Account'], response_class=JSONResponse)
@enveloped
async def forget_password(data: ForgetPasswordInput) -> None:
    await service.public.forget_password(username=data.username, account_email=data.email)


class ForgetUsernameInput(BaseModel):
    email: str


@router.post('/account/forget-username', tags=['Account'], response_class=JSONResponse)
@enveloped
async def forget_password(data: ForgetUsernameInput) -> None:
    await service.public.forget_username(account_email=data.email)
