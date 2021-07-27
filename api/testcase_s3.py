from fastapi import File, UploadFile

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
async def upload_testcase(testcase_id: int, file: UploadFile = File(...)) -> None:
    await s3.testcase.upload_input(testcase_id=testcase_id, file=file)

    '''
    s3_file = await s3.testcase.upload_input(testcase_id=testcase_id, file=file)
    id_ = await db.s3_file.add(bucket=s3_file.bucket, key=s3_file.key)
    return id_
    '''


