import typing

import persistence.database as db
import persistence.s3 as s3

browse_with_problem_id = db.assisting_data.browse_with_problem_id
read = db.assisting_data.read
delete = db.assisting_data.delete


async def add(file: typing.IO, filename: str, problem_id: int) -> int:
    bucket, key = await s3.assisting_data.upload(file=file)

    s3_file_uuid = await db.s3_file.add(bucket=bucket, key=key, filename=filename)

    assisting_data_id = await db.assisting_data.add(problem_id=problem_id, s3_file_uuid=s3_file_uuid)

    return assisting_data_id


async def edit(file: typing.IO, filename: str, assisting_data_id: int) -> None:
    bucket, key = await s3.assisting_data.upload(file=file)

    s3_file_uuid = await db.s3_file.add(bucket=bucket, key=key, filename=filename)

    await db.assisting_data.edit(assisting_data_id=assisting_data_id, s3_file_uuid=s3_file_uuid)
