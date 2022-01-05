import aioboto3

from base import mcs
from config import S3Config


class S3Handler(metaclass=mcs.Singleton):
    def __init__(self):
        self._session = aioboto3.Session()
        self._client = None  # Need to be init/closed manually
        self._resource = None  # Need to be init/closed manually

        self._buckets = {}

    async def initialize(self, s3_config: S3Config):
        self._client = await self._session.client(
            's3',
            endpoint_url=s3_config.endpoint,
            aws_access_key_id=s3_config.access_key,
            aws_secret_access_key=s3_config.secret_key,
        ).__aenter__()
        self._resource = await self._session.resource(
            's3',
            endpoint_url=s3_config.endpoint,
            aws_access_key_id=s3_config.access_key,
            aws_secret_access_key=s3_config.secret_key,
        ).__aenter__()

    async def close(self):
        if self._client is not None:
            await self._client.close()
        if self._resource is not None:
            await self._resource.close()

    async def create_bucket(self, bucket_name):
        return await self._resource.Bucket(bucket_name)

    async def get_bucket(self, bucket_name):
        """
        If the bucket requested is not yet created, will create the bucket.
        """
        try:
            return self._buckets[bucket_name]
        except KeyError:
            bucket = await self.create_bucket(bucket_name)
            self._buckets[bucket_name] = bucket
            return bucket

    async def sign_url(self, bucket: str, key: str, as_filename: str, expire_secs: int, as_attachment: bool) -> str:
        return await self._client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket,
                'Key': key,
                'ResponseContentDisposition': f'{"attachment;" if as_attachment else ""}'
                                              f'filename="{as_filename}";',
            },
            ExpiresIn=expire_secs,
        )

    async def get_file_content(self, bucket: str, key: str) -> bytes:
        infile_object = await self._client.get_object(Bucket=bucket, Key=key)
        infile_content = await infile_object['Body'].read()
        return infile_content

    async def put_object(self, bucket: str, key: str, body) -> None:
        await self._client.put_object(Bucket=bucket, Key=key, Body=body)


s3_handler = S3Handler()


# For import usage
from . import (
    tools,

    testdata,
    submission,
    essay_submission,
    assisting_data,
    temp,
    customized_code,
)
