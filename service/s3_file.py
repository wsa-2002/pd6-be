from const import S3_EXPIRE_SECS
from persistence import database as db, s3


read = db.s3_file.read


async def sign_url(bucket: str, key: str, filename: str, as_attachment: bool) -> str:
    return await s3.tools.sign_url(bucket=bucket, key=key, expire_secs=S3_EXPIRE_SECS, filename=filename,
                                   as_attachment=as_attachment)


