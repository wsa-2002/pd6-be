from persistence import email

from config import service_config


async def send_email_verification_email(
        to: str,
        code: str,
        subject='PDOGS Email Verification',
):
    content = fr"""
Please verify your email with the following url:
{service_config.url}/email-verification?code={code}
"""
    await email.send(to=to, subject=subject, content=content)
