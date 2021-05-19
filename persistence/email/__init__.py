from email.message import EmailMessage

import aiosmtplib

from config import smtp_config


async def send(to: str, subject: str, content: str):
    message = EmailMessage()
    message["From"] = f"{smtp_config.account}@{smtp_config.host}"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(content)

    await aiosmtplib.send(message=message, hostname=smtp_config.host, port=smtp_config.port)
