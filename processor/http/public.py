from uuid import UUID

from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import app_config
import exceptions as exc
from middleware import APIRouter, JSONResponse, enveloped
import persistence.database as db
from persistence import email
from util import model

router = APIRouter(tags=['Public'])


@router.get("/", status_code=200, response_class=HTMLResponse)
async def default_page():
    doc_paths = []
    if _url := app_config.docs_url:
        doc_paths.append(f'<a href="{_url}">{_url}</a>')
    if _url := app_config.redoc_url:
        doc_paths.append(f'<a href="{_url}">{_url}</a>')
    return fr"""
{' or '.join(doc_paths)}
<br>
<br>
<img src="https://i.imgur.com/dBUZ3Ig.png" alt="I am not PDOGS" height="90%">
"""


# Warning: this location is statically used in email string
# Use "get" for convenience (access from browser)
@router.get('/email-verification', tags=['Account', 'Student Card'])
@router.post('/email-verification', tags=['Account', 'Student Card'])
@enveloped
async def email_verification(code: UUID):
    await db.account.verify_email(code=code)


class ForgetPasswordInput(BaseModel):
    username: str
    email: model.CaseInsensitiveEmailStr


@router.post('/account/forget-password', tags=['Account'], response_class=JSONResponse)
@enveloped
async def forget_password(data: ForgetPasswordInput) -> None:
    try:
        accounts = await db.account.browse_by_email(data.email, username=data.username)
    except exc.persistence.NotFound:
        return  # not to let user know there is no related accounts

    # should only be one account, since username is given
    for account in accounts:
        code = await db.account.add_email_verification(email=data.email, account_id=account.id)
        await email.forget_password.send(to=data.email, code=code)


class ForgetUsernameInput(BaseModel):
    email: model.CaseInsensitiveEmailStr


@router.post('/account/forget-username', tags=['Account'], response_class=JSONResponse)
@enveloped
async def forget_username(data: ForgetUsernameInput) -> None:
    try:
        accounts = await db.account.browse_by_email(data.email, search_exhaustive=True)
    except exc.persistence.NotFound:
        return  # not to let user know there is no related accounts

    await email.forget_username.send(to=data.email, accounts=accounts)
