import io
import zipfile

import persistence.database as db
import persistence.s3 as s3
import service.s3_file as s3_tool
import persistence.email as email


add = db.essay.add
read = db.essay.read
browse = db.essay.browse
edit = db.essay.edit
delete = db.essay.delete


async def download_all(account_id: int, essay_id: int, filename: str, as_attachment: bool) -> None:
    result = await db.essay_submission.browse(essay_id=essay_id)
    files = {}
    for essay_submission in result:
        s3_file = await db.s3_file.read(s3_file_uuid=essay_submission.content_file_uuid)
        files[essay_submission.filename] = s3_file.key

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zipper:
        for filename in files:
            infile_content = await s3.essay_submission.get_file_content(key=files[filename])
            zipper.writestr(filename, infile_content)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=filename, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
