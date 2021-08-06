import aioboto3

from base import mcs
from config import S3Config


class S3Handler(metaclass=mcs.Singleton):
    def __init__(self):
        self._session = aioboto3.Session()
        self._resource = None  # Need to be init/closed manually

        self._buckets = {}

    async def initialize(self, s3_config: S3Config):
        self._resource = await self._session.resource(
            's3',
            endpoint_url=s3_config.endpoint,
            aws_access_key_id=s3_config.access_key,
            aws_secret_access_key=s3_config.secret_key,
        ).__aenter__()

    async def close(self):
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


s3_handler = S3Handler()


# For import usage
from . import (
    testcase,
    submission,
)
