from base import do
from persistence import database as db, s3


read = db.s3_file.read


EXPIRE_SECS = 86400  # 1 day


async def sign_url(s3_file: do.S3File, as_attachment: bool) -> str:
    return await s3.tools.sign_url(s3_file=s3_file, expire_secs=EXPIRE_SECS, as_attachment=as_attachment)
