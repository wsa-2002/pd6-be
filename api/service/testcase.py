import typing

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
    bucket, key = await s3.testcase.upload_input(file=file, filename=filename)
    file_id = await db.s3_file.add(bucket=bucket, key=key)
    await db.testcase.edit(testcase_id=testcase_id, input_file_uuid=file_id)


async def edit_output(testcase_id: int, file: typing.IO, filename: str) -> None:
    # 流程: 先 upload 到 s3 取得 bucket, key
    #       bucket, key 進 s3_file db 得到 file id
    #       file_id 進 testcase db
    bucket, key = await s3.testcase.upload_output(file=file, filename=filename)
    file_id = await db.s3_file.add(bucket=bucket, key=key)
    await db.testcase.edit(testcase_id=testcase_id, input_file_uuid=file_id)


delete_input_data = db.testcase.delete_input_data
delete_output_data = db.testcase.delete_output_data
