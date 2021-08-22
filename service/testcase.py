import typing
import uuid

import persistence.database as db
import persistence.s3 as s3


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
