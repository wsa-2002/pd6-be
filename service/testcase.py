import io
import zipfile
import typing
import uuid

import exceptions as exc
import log

import persistence.database as db
import persistence.s3 as s3
import service.s3_file as s3_tool
import persistence.email as email


SAMPLE_FILENAME = 'sample_testcase.zip'
NON_SAMPLE_FILENAME = 'non_sample_testcase.zip'


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


async def download_all_sample(account_id: int, problem_id: int, as_attachment: bool) -> None:
    result = await db.testcase.browse(problem_id=problem_id, is_sample=True, include_disabled=True)
    files = []
    for testcase in result:
        try:
            input_s3_file = await db.s3_file.read(s3_file_uuid=testcase.input_file_uuid)
            files.append((input_s3_file, testcase.input_filename))
            output_s3_file = await db.s3_file.read(s3_file_uuid=testcase.output_file_uuid)
            files.append((output_s3_file, testcase.output_filename))
        except:
            pass

    zip_buffer = await s3.tools._zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=SAMPLE_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)


async def download_all_non_sample(account_id: int, problem_id: int, as_attachment: bool) -> None:
    result = await db.testcase.browse(problem_id=problem_id, is_sample=False, include_disabled=True)
    files = []
    for testcase in result:
        try:
            input_s3_file = await db.s3_file.read(s3_file_uuid=testcase.input_file_uuid)
            files.append((input_s3_file, testcase.input_filename))
            output_s3_file = await db.s3_file.read(s3_file_uuid=testcase.output_file_uuid)
            files.append((output_s3_file, testcase.output_filename))
        except:
            pass

    zip_buffer = await s3.tools._zipper(files=files)

    s3_file = await s3.temp.put_object(body=zip_buffer.getvalue())

    file_url = await s3_tool.sign_url(bucket=s3_file.bucket, key=s3_file.key,
                                      filename=NON_SAMPLE_FILENAME, as_attachment=as_attachment)

    account, student_card = await db.account_vo.read_with_default_student_card(account_id=account_id)
    await email.notification.send_file_download_url(to=student_card.email, file_url=file_url)
