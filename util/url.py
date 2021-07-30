from base import do
from config import s3_config


def join_s3(s3_file: do.S3File) -> str:
    return f"{s3_config.endpoint}/minio/{s3_file.bucket}/{s3_file.key}"
