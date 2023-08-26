from typing import Sequence
from uuid import UUID

from base import do

from .base import FetchAll, FetchOne, OnlyExecute


async def browse(problem_id: int, include_deleted=False) -> Sequence[do.AssistingData]:
    async with FetchAll(
            event='browse assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, filename, is_deleted'
                fr'  FROM assisting_data'
                fr' WHERE problem_id = %(problem_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER by id ASC',
            problem_id=problem_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid,
                                 filename=filename, is_deleted=is_deleted)
                for (id_, problem_id, s3_file_uuid, filename, is_deleted) in records]


async def read(assisting_data_id: int, include_deleted=False) -> do.AssistingData:
    async with FetchOne(
            event='read assisting data',
            sql=fr'SELECT id, problem_id, s3_file_uuid, filename, is_deleted'
                fr'  FROM assisting_data'
                fr' WHERE id = %(assisting_data_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            assisting_data_id=assisting_data_id,
    ) as (id_, problem_id, s3_file_uuid, filename, is_deleted):
        return do.AssistingData(id=id_, problem_id=problem_id, s3_file_uuid=s3_file_uuid,
                                filename=filename, is_deleted=is_deleted)


async def add(problem_id: int, s3_file_uuid: UUID, filename: str) -> int:
    async with FetchOne(
            event='add assisting data',
            sql=r'INSERT INTO assisting_data'
                r'            (problem_id, s3_file_uuid, filename, is_deleted)'
                r'     VALUES (%(problem_id)s, %(s3_file_uuid)s, %(filename)s, %(is_deleted)s)'
                r'  RETURNING id',
            problem_id=problem_id, s3_file_uuid=s3_file_uuid, filename=filename, is_deleted=False,
    ) as (id_,):
        return id_


async def edit(assisting_data_id: int, s3_file_uuid: UUID, filename: str):
    async with OnlyExecute(
            event='update assisting data',
            sql=r'UPDATE assisting_data'
                r'   SET s3_file_uuid = %(s3_file_uuid)s, filename = %(filename)s'
                r' WHERE id = %(assisting_data_id)s',
            assisting_data_id=assisting_data_id, filename=filename,
            s3_file_uuid=s3_file_uuid,
    ):
        pass


async def delete(assisting_data_id: int) -> None:
    async with OnlyExecute(
            event='soft delete assisting data',
            sql=r'UPDATE assisting_data'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(assisting_data_id)s',
            assisting_data_id=assisting_data_id, is_deleted=True,
    ):
        pass
