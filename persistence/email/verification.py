from email.message import EmailMessage

import log
from config import service_config, smtp_config
from persistence.email import smtp_handler


async def send(to: str, code: str, subject='PDOGS Email Verification'):
    message = EmailMessage()
    message["From"] = f"{smtp_config.username}@{smtp_config.host}"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(fr"""
Please verify your email with the following url:
{service_config.url}/email-verification?code={code}
""")

    async with smtp_handler.client:
        await smtp_handler.client.send_message(message)
