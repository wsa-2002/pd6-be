import aioboto3

from base import mcs
from config import S3Config


class S3Handler(metaclass=mcs.Singleton):
    def __init__(self):
        self._client = None  # Need to be init/closed manually

    async def initialize(self, s3_config: S3Config):
        if self._client is None:
            session = aioboto3.Session()
            self._client = await session.client(
                's3',
                endpoint_url=f'https://{s3_config.host}:{s3_config.port}',
                aws_access_key_id=s3_config.access_key,
                aws_secret_access_key=s3_config.secret_key
            )

    async def close(self):
        if self._client is not None:
            self._client.close()

    @property
    def client(self):
        return self._client


s3_handler = S3Handler()

# For import usage
from . import (
    file,
)
