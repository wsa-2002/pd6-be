import aioboto3

from base import mcs
from config import S3Config

session = aioboto3.Session()


class S3Handler(metaclass=mcs.Singleton):
    def __init__(self):
        self._resource = None  # Need to be init/closed manually

    async def initialize(self, s3_config: S3Config):
        if self._resource is None:
            async with session.resource(
                    's3',
                    endpoint_url=f'https://{s3_config.host}:{s3_config.port}',
                    aws_access_key_id=s3_config.access_key,
                    aws_secret_access_key=s3_config.secret_key,
            ) as resource:
                self._resource = resource

    async def close(self):
        if self._resource is not None:
            self._resource.close()

    @property
    def resource(self):
        return self._resource


s3_handler = S3Handler()

# For import usage
from . import (
    testcase,
)
