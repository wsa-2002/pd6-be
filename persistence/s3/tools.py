from base import do

from . import s3_handler


async def sign_url(s3_file: do.S3File, expire_secs: int, filename: str, as_attachment: bool) -> str:
    return await s3_handler.sign_url(
        bucket=s3_file.bucket,
        key=s3_file.key,
        as_filename=filename,
        expire_secs=expire_secs,
        as_attachment=as_attachment,
    )
