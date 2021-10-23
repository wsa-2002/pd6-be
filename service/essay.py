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
    essay_submissions = await db.essay_submission.browse_with_essay_id(essay_id=essay_id)
    s3_files = await db.s3_file.browse_with_uuids(essay_submission.content_file_uuid
                                                  for essay_submission in essay_submissions)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_STORED, allowZip64=False) as zipper:
        for essay_submission, s3_file in zip(essay_submissions, s3_files):
            infile_content = await s3.tools.get_file_content(bucket=s3_file.bucket, key=s3_file.key)
            zipper.writestr(essay_submission.filename, infile_content)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=ESSAY_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
