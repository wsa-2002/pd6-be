from base import do

from . import s3_handler


async def sign_url(bucket: str, key: str, expire_secs: int, filename: str, as_attachment: bool) -> str:
    return await s3_handler.sign_url(
        bucket=bucket,
        key=key,
        as_filename=filename,
        expire_secs=expire_secs,
        as_attachment=as_attachment,
    )


async def sign_url_from_do(s3_file: do.S3File, expire_secs: int, filename: str, as_attachment: bool) -> str:
    return await sign_url(
        bucket=s3_file.bucket,
        key=s3_file.key,
        filename=filename,
        expire_secs=expire_secs,
        as_attachment=as_attachment,
    )


async def get_file_content(bucket: str, key: str):
    """
    :return: infile content
    """
    return await s3_handler.get_file_content(bucket=bucket, key=key)
