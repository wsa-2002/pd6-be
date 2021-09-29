from email.message import EmailMessage

import log
from base import do
from config import service_config, smtp_config
from persistence.email import smtp_handler


async def send(to: str, *accounts: do.Account, subject='PDOGS Email Verification'):
    message = EmailMessage()
    message["From"] = f"{smtp_config.username}@{smtp_config.host}"
    message["To"] = to
    message["Subject"] = subject
    joined_usernames = '\n'.join(account.username for account in accounts)
    message.set_content(fr"""
Your username{'s are' if len(accounts) > 1 else ' is'}:
{joined_usernames}
""")

    async with smtp_handler.client:
        await smtp_handler.client.send_message(message)
