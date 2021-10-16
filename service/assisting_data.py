import io
import zipfile
import typing
import uuid

import persistence.database as db
import persistence.s3 as s3
import service.s3_file as s3_tool
import persistence.email as email


ASSISTING_DATA_FILENAME = 'assisting_data.zip'


browse_with_problem_id = db.assisting_data.browse
read = db.assisting_data.read
delete = db.assisting_data.delete


async def add(file: typing.IO, filename: str, problem_id: int) -> int:
    file_uuid = uuid.uuid4()
    s3_file = await s3.assisting_data.upload(file=file, file_uuid=file_uuid)

    s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    assisting_data_id = await db.assisting_data.add(problem_id=problem_id, s3_file_uuid=s3_file_uuid, filename=filename)

    return assisting_data_id


async def edit(file: typing.IO, filename: str, assisting_data_id: int) -> None:
    file_uuid = uuid.uuid4()
    s3_file = await s3.assisting_data.upload(file=file, file_uuid=file_uuid)

    s3_file_uuid = await db.s3_file.add_with_do(s3_file=s3_file)

    await db.assisting_data.edit(assisting_data_id=assisting_data_id, s3_file_uuid=s3_file_uuid, filename=filename)


async def download_all(account_id: int, problem_id: int, as_attachment: bool) -> None:
    result = await db.assisting_data.browse(problem_id=problem_id)
    files = []
    for assisting_data in result:
        s3_file = await db.s3_file.read(s3_file_uuid=assisting_data.s3_file_uuid)
        files.append((s3_file, assisting_data.filename))

    zip_buffer = await s3.tools.zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=ASSISTING_DATA_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
