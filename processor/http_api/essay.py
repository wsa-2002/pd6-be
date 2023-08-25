from typing import Optional

from fastapi import BackgroundTasks
from pydantic import BaseModel

import const
import log
from base.enum import RoleType
from base import do
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth
import persistence.database as db
import service
from persistence import s3, email
import util
from util import model
from util.context import context

router = APIRouter(
    tags=['Essay'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/essay/{essay_id}')
@enveloped
async def read_essay(essay_id: int) -> do.Essay:
    """
    ### 權限
    - class normal
    """
    class_role = await service.rbac.get_class_role(context.account.id, essay_id=essay_id)
    if class_role < RoleType.normal:
        raise exc.NoPermission

    essay = await db.essay.read(essay_id=essay_id)
    challenge = await db.challenge.read(essay.challenge_id)
    is_scheduled = challenge.start_time > context.request_time

    if is_scheduled and class_role < RoleType.manager:
        raise exc.NoPermission

    return essay


class EditEssayInput(BaseModel):
    title: Optional[str] = model.can_omit
    challenge_label: Optional[str] = model.can_omit
    description: Optional[str] = model.can_omit


@router.patch('/essay/{essay_id}')
@enveloped
async def edit_essay(essay_id: int, data: EditEssayInput) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, essay_id=essay_id):
        raise exc.NoPermission

    await db.essay.edit(essay_id=essay_id, setter_id=context.account.id, title=data.title,
                        challenge_label=data.challenge_label, description=data.description)


@router.delete('/essay/{essay_id}')
@enveloped
async def delete_essay(essay_id: int) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, essay_id=essay_id):
        raise exc.NoPermission

    await db.essay.delete(essay_id=essay_id)


@router.post('/essay/{essay_id}/all-essay-submission')
@enveloped
async def download_all_essay_submission(essay_id: int, as_attachment: bool,
                                        background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    if not await service.rbac.validate_class(context.account.id, RoleType.manager, essay_id=essay_id):
        raise exc.NoPermission

    # Hardcode for PBC 110-1: Only allow specific managers to download final project data
    if essay_id in (2, 3, 4) \
            and (await db.essay.read(essay_id)).challenge_id == 367 \
            and context.account.id not in (14, 1760, 2646, 2648):
        raise exc.NoPermission

    async def _task() -> None:
        log.info("Start download all essay submission")

        s3_file = await service.downloader.all_essay_submissions(essay_id=essay_id)
        file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                           filename='essay_submission.zip', as_attachment=as_attachment,
                                           expire_secs=const.S3_MANAGER_EXPIRE_SECS)

        log.info("URL signed, sending email")

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=context.account.id)
        await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)

        log.info('Done')

    util.background_task.launch(background_tasks, _task)
