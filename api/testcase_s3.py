from fastapi import File, UploadFile
from fastapi.responses import JSONResponse

from middleware import APIRouter, response, enveloped, auth
import persistence.s3 as s3
import persistence.database as db


router = APIRouter(
    tags=['S3 Persistence'],
    route_class=auth.APIRoute,
    default_response_class=response.JSONResponse,
)


@router.post('/testcase/{testcase_id}/input-data')
@enveloped
async def upload_testcase(filename: str, testcase_id: int, file: UploadFile = File(...)) -> None:
    bucket, key = await s3.testcase.upload_input(file=file.file, filename=filename, testcase_id=testcase_id)
    await db.s3_file.add(bucket=bucket, key=key)


@router.post('/testcase/download')
@enveloped
async def download_testcase(key: str, filename: str) -> None:
    bucket = await s3.testcase.download(key=key, filename=filename)


@router.post('/testcase/delete')
@enveloped
async def delete_testcase(s3_file_id: int) -> None:
    await s3.testcase.delete(s3_file_id=s3_file_id)


@router.post('/testcase/check-exist')
@enveloped
async def check_testcase(key: str):
    s3_file = await db.s3_file.read_by_key(key=key)
    if s3_file is None:

    return {"detail": f"{s3_file.id}!!!"}
    '''
    s3_file = await s3.testcase.upload_input(testcase_id=testcase_id, file=file)
    id_ = await db.s3_file.add(bucket=s3_file.bucket, key=s3_file.key)
    return id_
    '''


