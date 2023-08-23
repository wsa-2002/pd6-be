from email.message import EmailMessage

from config import service_config, smtp_config
from persistence.email import smtp_handler


async def send(to: str, code: str, subject='PDOGS Email Verification'):
    message = EmailMessage()
    message["From"] = f"{smtp_config.username}@{smtp_config.host}"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(fr"""
Please click on the following link to reset your password:
{service_config.url}/reset-password?code={code}
""")  # link to FE reset password page, not BE

    await smtp_handler.send_message(message)
