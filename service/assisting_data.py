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
    assisting_datas = await db.assisting_data.browse(problem_id=problem_id)
    s3_files = await db.s3_file.browse_with_uuids(assisting_data.s3_file_uuid for assisting_data in assisting_datas)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_STORED, allowZip64=False) as zipper:
        for assisting_data, s3_file in zip(assisting_datas, s3_files):
            if not s3_file:
                continue
            infile_content = await s3.tools.get_file_content(bucket=s3_file.bucket, key=s3_file.key)
            zipper.writestr(assisting_data.filename, infile_content)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=ASSISTING_DATA_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
