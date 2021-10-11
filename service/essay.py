import io
import zipfile

import persistence.database as db
import persistence.s3 as s3
import service.s3_file as s3_tool
import persistence.email as email


ESSAY_FILENAME = 'essay_submission.zip'


add = db.essay.add
read = db.essay.read
browse = db.essay.browse
edit = db.essay.edit
delete = db.essay.delete


async def download_all(account_id: int, essay_id: int, as_attachment: bool) -> None:
    result = await db.essay_submission.browse_with_essay_id(essay_id=essay_id)
    files = []
    for essay_submission in result:
        s3_file = await db.s3_file.read(s3_file_uuid=essay_submission.content_file_uuid)
        files.append((s3_file, essay_submission.filename))

    zip_buffer = await s3.tools._zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=ESSAY_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
