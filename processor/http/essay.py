from typing import Optional

from fastapi import BackgroundTasks
from pydantic import BaseModel

import log
from base.enum import RoleType
from base import do
import exceptions as exc
from middleware import APIRouter, response, enveloped, auth, Request
import persistence.database as db
import service
from persistence import s3, email
import util
from util import model

router = APIRouter(
    tags=['Essay'],
    default_response_class=response.JSONResponse,
    dependencies=auth.doc_dependencies,
)


@router.get('/essay/{essay_id}')
@enveloped
async def read_essay(essay_id: int, request: Request) -> do.Essay:
    """
    ### 權限
    - class normal
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    essay = await db.essay.read(essay_id=essay_id)
    challenge = await db.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)
    class_role = await service.rbac.get_role(request.account.id, class_id=challenge.class_id)

    is_scheduled = challenge.start_time > request.time

    if not (is_scheduled and class_role >= RoleType.manager
            or not is_scheduled and class_role >= RoleType.normal):
        raise exc.NoPermission

    return essay


class EditEssayInput(BaseModel):
    title: Optional[str] = model.can_omit
    challenge_label: Optional[str] = model.can_omit
    description: Optional[str] = model.can_omit


@router.patch('/essay/{essay_id}')
@enveloped
async def edit_essay(essay_id: int, data: EditEssayInput, request: Request) -> None:
    """
    ### 權限
    - class manager
    """
    essay = await db.essay.read(essay_id=essay_id)
    challenge = await db.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)

    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.essay.edit(essay_id=essay.id, setter_id=request.account.id, title=data.title,
                        challenge_label=data.challenge_label, description=data.description)


@router.delete('/essay/{essay_id}')
@enveloped
async def delete_essay(essay_id: int, request: Request) -> None:
    """
    ### 權限
    - class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    essay = await db.essay.read(essay_id=essay_id)
    challenge = await db.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)
    if not service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    await db.essay.delete(essay_id=essay_id)


@router.post('/essay/{essay_id}/all-essay-submission')
@enveloped
async def download_all_essay_submission(essay_id: int, request: Request, as_attachment: bool,
                                        background_tasks: BackgroundTasks) -> None:
    """
    ### 權限
    - class manager
    """
    # 因為需要 class_id 才能判斷權限，所以先 read 再判斷要不要噴 NoPermission
    essay = await db.essay.read(essay_id=essay_id)
    challenge = await db.challenge.read(essay.challenge_id, include_scheduled=True, ref_time=request.time)
    if not await service.rbac.validate(request.account.id, RoleType.manager, class_id=challenge.class_id):
        raise exc.NoPermission

    async def _task() -> None:
        log.info("Start download all essay submission")

        s3_file = await service.downloader.all_essay_submissions(essay_id=essay_id)
        file_url = await s3.tools.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                           filename='essay_submission.zip', as_attachment=as_attachment)

        log.info("URL signed, sending email")

        account, student_card = await db.account_vo.read_with_default_student_card(account_id=request.account.id)
        await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)

        log.info('Done')

    util.background_task.launch(background_tasks, _task)
