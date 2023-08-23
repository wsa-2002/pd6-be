from typing import Collection

from email.message import EmailMessage

from base import do
from config import smtp_config
from persistence.email import smtp_handler


async def send(to: str, accounts: Collection[do.Account], subject='PDOGS Email Notification'):
    message = EmailMessage()
    message["From"] = f"{smtp_config.username}@{smtp_config.host}"
    message["To"] = to
    message["Subject"] = subject
    joined_usernames = '\n'.join(account.username for account in accounts)
    message.set_content(fr"""
Your username{'s are' if len(accounts) > 1 else ' is'}:
{joined_usernames}
""")

    await smtp_handler.send_message(message)
