import io
import zipfile
import typing
import uuid

import exceptions as exc

import persistence.database as db
import persistence.s3 as s3
import service.s3_file as s3_tool
import persistence.email as email


add = db.testcase.add
browse = db.testcase.browse
read = db.testcase.read
edit = db.testcase.edit
delete = db.testcase.delete


async def edit_input(testcase_id: int, file: typing.IO, filename: str) -> None:
    # 流程: 先 upload 到 s3 取得 bucket, key
    #       bucket, key 進 s3_file db 得到 file id
    #       file_id 進 testcase db
    file_uuid = uuid.uuid4()
    s3_file = await s3.testdata.upload(file=file, file_uuid=file_uuid)
    file_id = await db.s3_file.add_with_do(s3_file=s3_file)
    await db.testcase.edit(testcase_id=testcase_id, input_file_uuid=file_id, input_filename=filename)


async def edit_output(testcase_id: int, file: typing.IO, filename: str) -> None:
    # 流程: 先 upload 到 s3 取得 bucket, key
    #       bucket, key 進 s3_file db 得到 file id
    #       file_id 進 testcase db
    file_uuid = uuid.uuid4()
    s3_file = await s3.testdata.upload(file=file, file_uuid=file_uuid)
    file_id = await db.s3_file.add_with_do(s3_file=s3_file)
    await db.testcase.edit(testcase_id=testcase_id, output_file_uuid=file_id, output_filename=filename)


delete_input_data = db.testcase.delete_input_data
delete_output_data = db.testcase.delete_output_data


async def download_all_sample(account_id: int, problem_id: int, filename: str, as_attachment: bool) -> None:
    result = await db.testcase.browse(problem_id=problem_id)
    files = {}
    for testcase in result:
        if testcase.is_sample:
            try:
                input_s3_file = await db.s3_file.read(s3_file_uuid=testcase.input_file_uuid)
                files[testcase.input_filename] = input_s3_file.key
                output_s3_file = await db.s3_file.read(s3_file_uuid=testcase.output_file_uuid)
                files[testcase.output_filename] = output_s3_file.key
            except:
                pass

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zipper:
        for filename in files:
            infile_content = await s3.testdata.get_file_content(key=files[filename])
            zipper.writestr(filename, infile_content)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=filename, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)


async def download_all_non_sample(account_id: int, problem_id: int, filename: str, as_attachment: bool) -> None:
    result = await db.testcase.browse(problem_id=problem_id)
    files = {}
    for testcase in result:
        if not testcase.is_sample:
            try:
                input_s3_file = await db.s3_file.read(s3_file_uuid=testcase.input_file_uuid)
                files[testcase.input_filename] = input_s3_file.key
                output_s3_file = await db.s3_file.read(s3_file_uuid=testcase.output_file_uuid)
                files[testcase.output_filename] = output_s3_file.key
            except:
                pass

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zipper:
        for filename in files:
            infile_content = await s3.testdata.get_file_content(key=files[filename])
            zipper.writestr(filename, infile_content)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=filename, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
