import aiosmtplib

from base import mcs
from config import SMTPConfig


class SMTPHandler(metaclass=mcs.Singleton):
    def __init__(self):
        self._client: aiosmtplib.SMTP = None  # Need to be init/closed manually

    async def initialize(self, smtp_config: SMTPConfig):
        if self._client is None:
            self._client = aiosmtplib.SMTP(
                hostname=smtp_config.host,
                port=smtp_config.port,
                username=smtp_config.username,
                password=smtp_config.password,
                use_tls=smtp_config.use_tls,
            )

    async def close(self):
        if self._client is not None:
            self._client.close()

    @property
    def client(self):
        return self._client


smtp_handler = SMTPHandler()


# For import usage
from . import (
    verification,
    notification,
    forget_password,
    forget_username,
)
