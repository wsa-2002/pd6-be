from base import do
from persistence import database as db, s3


read = db.s3_file.read


EXPIRE_SECS = 86400  # 1 day


async def sign_url(bucket: str, key: str, filename: str, as_attachment: bool) -> str:
    return await s3.tools.sign_url(bucket=bucket, key=key, expire_secs=EXPIRE_SECS, filename=filename,
                                   as_attachment=as_attachment)
