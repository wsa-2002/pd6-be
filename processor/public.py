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
@router.get('/email-verification', tags=['Account', 'Student Card'], response_class=HTMLResponse)
@router.post('/email-verification', tags=['Account', 'Student Card'], response_class=HTMLResponse)
async def email_verification(code: str):
    try:
        await service.account.verify_email(code=code)
    except exc.persistence.NotFound:
        return 'Your verification code is not valid.'
    else:
        return 'Your email has been verified.'


class ForgetPasswordInput(BaseModel):
    email: str


@router.post('/account/forget-password', tags=['Account'], response_class=JSONResponse)
@enveloped
async def forget_password(data: ForgetPasswordInput) -> None:
    await service.public.forget_password(account_email=data.email)
