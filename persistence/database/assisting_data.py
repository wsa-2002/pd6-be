from typing import Sequence, Tuple
from uuid import UUID

from base import do

from .base import SafeExecutor


async def browse(include_deleted=False) -> Sequence[do.AssistingData]:
    async with SafeExecutor(
            event='browse assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, filename, is_deleted'
                fr'  FROM assisting_data'
                fr'{" WHERE NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER by id ASC',
            fetch='all',
    ) as records:
        return [do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid,
                                 filename=filename, is_deleted=is_deleted)
                for (id_, problem_id, s3_file_uuid, filename, is_deleted) in records]


async def browse_with_problem_id(problem_id: int, include_deleted=False) -> Sequence[do.AssistingData]:
    async with SafeExecutor(
            event='browse assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, filename, is_deleted'
                fr'  FROM assisting_data'
                fr' WHERE problem_id = %(problem_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER by id ASC',
            problem_id=problem_id,
            fetch='all',
    ) as records:
        return [do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid,
                                 filename=filename, is_deleted=is_deleted)
                for (id_, problem_id, s3_file_uuid, filename, is_deleted) in records]


async def browse_with_problem_and_s3_file(problem_id: int, include_deleted=False) \
        -> Sequence[Tuple[do.AssistingData, do.S3File]]:
    async with SafeExecutor(
            event='browse assisting data with problem and s3_file',
            sql=fr'SELECT assisting_data.id, assisting_data.problem_id, assisting_data.s3_file_uuid,'
                fr'       assisting_data.filename, assisting_data.is_deleted,'
                fr'       s3_file.uuid, s3_file.bucket, s3_file.key'
                fr'  FROM assisting_data'
                fr' INNER JOIN s3_file'
                fr'         ON s3_file.uuid = assisting_data.s3_file_uuid'
                fr' WHERE assisting_data.problem_id = %(problem_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER by assisting_data.id ASC',
            problem_id=problem_id,
            fetch='all',
    ) as records:
        return [(do.AssistingData(id=assisting_data_id, problem_id=problem_id, s3_file_uuid=s3_file_uuid,
                                  filename=filename, is_deleted=is_deleted),
                 do.S3File(uuid=uuid, bucket=bucket, key=key))
                for (assisting_data_id, problem_id, s3_file_uuid, filename, is_deleted,
                     uuid, bucket, key) in records]


async def read(assisting_data_id: int, include_deleted=False) -> do.AssistingData:
    async with SafeExecutor(
            event='read assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, filename, is_deleted'
                fr'  FROM assisting_data'
                fr' WHERE id = %(assisting_data_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            assisting_data_id=assisting_data_id,
            fetch=1,
    ) as (id_, problem_id, s3_file_uuid, filename, is_deleted):
        return do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid,
                                filename=filename, is_deleted=is_deleted)


async def add(problem_id: int, s3_file_uuid: UUID, filename: str) -> int:
    async with SafeExecutor(
            event='add assisting data',
            sql=fr'INSERT INTO assisting_data'
                fr'            (problem_id, s3_file_uuid, filename, is_deleted)'
                fr'     VALUES (%(problem_id)s, %(s3_file_uuid)s, %(filename)s, %(is_deleted)s)'
                fr'  RETURNING id',
            problem_id=problem_id, s3_file_uuid=s3_file_uuid, filename=filename, is_deleted=False,
            fetch=1,
    ) as (id_,):
        return id_


async def edit(assisting_data_id: int, s3_file_uuid: UUID, filename: str):
    async with SafeExecutor(
            event='update assisting data',
            sql=fr'UPDATE assisting_data'
                fr'   SET s3_file_uuid = %(s3_file_uuid)s, filename = %(filename)s'
                fr' WHERE id = %(assisting_data_id)s',
            assisting_data_id=assisting_data_id, filename=filename,
            s3_file_uuid=s3_file_uuid,
    ):
        pass


async def delete(assisting_data_id: int) -> None:
    async with SafeExecutor(
            event='soft delete assisting data',
            sql=fr'UPDATE assisting_data'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(assisting_data_id)s',
            assisting_data_id=assisting_data_id, is_deleted=True,
    ):
        pass
