from typing import Sequence
from uuid import UUID

from base import do

from .base import SafeExecutor


async def browse(include_deleted=False) -> Sequence[do.AssistingData]:
    async with SafeExecutor(
            event='browse assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, is_deleted'
                fr'  FROM assisting_data'
                fr'{" WHERE NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER by id ASC',
            fetch='all',
    ) as records:
        return [do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid, is_deleted=is_deleted)
                for (id_, problem_id, s3_file_uuid, is_deleted) in records]


async def browse_with_problem_id(problem_id: int, include_deleted=False) -> Sequence[do.AssistingData]:
    async with SafeExecutor(
            event='browse assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, is_deleted'
                fr'  FROM assisting_data'
                fr' WHERE problem_id = %(problem)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER by id ASC',
            problem_id=problem_id,
            fetch='all',
    ) as records:
        return [do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid, is_deleted=is_deleted)
                for (id_, problem_id, s3_file_uuid, is_deleted) in records]


async def read(assisting_data_id: int, include_deleted=False) -> do.AssistingData:
    async with SafeExecutor(
            event='read assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, is_deleted'
                fr'  FROM assisting_data'
                fr' WHERE id = %(assisting_data_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            assisting_data_id=assisting_data_id,
            fetch=1,
    ) as (id_, problem_id, s3_file_uuid, is_deleted):
        return do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid, is_deleted=is_deleted)


async def add(problem_id: int, s3_file_uuid: UUID) -> int:
    async with SafeExecutor(
            event='add assisting data',
            sql=fr'INSERT INTO assisting_data'
                fr'            (problem_id, s3_file_uuid, is_deleted)'
                fr'     VALUES (%(problem_id)s, %(s3_file_uuid)s, %(is_deleted)s)'
                fr'  RETURNING id',
            problem_id=problem_id, s3_file_uuid=s3_file_uuid, is_deleted=False,
            fetch=1,
    ) as (id_,):
        return id_


async def edit(assisting_data_id: int, s3_file_uuid: UUID):
    async with SafeExecutor(
            event='update assisting data',
            sql=fr'UPDATE assisting_data'
                fr'   SET s3_file_uuid = %(s3_file_uuid)'
                fr' WHERE id = %(assisting_data_id)',
            assisting_data_id=assisting_data_id,
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
