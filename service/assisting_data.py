import typing
import uuid

import persistence.database as db
import persistence.s3 as s3

browse_with_problem_id = db.assisting_data.browse_with_problem_id
browse_with_s3_files = db.assisting_data.browse_with_s3_files
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
