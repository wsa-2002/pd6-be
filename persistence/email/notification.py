from email.message import EmailMessage

from config import service_config, smtp_config
from persistence.email import smtp_handler
from typing import Sequence


# for general msgs
async def send(to: Sequence[str], msg: str, subject='PDOGS Notification'):
    message = EmailMessage()
    message["From"] = f"{smtp_config.username}@{smtp_config.host}"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(msg)

    async with smtp_handler.client:
        await smtp_handler.client.send_message(message)


# update class manager change
async def notify_cm_change(tos: Sequence[str], account_id: int, class_id: int, operator_id: int):
    for to in tos:
        message = EmailMessage()
        message["From"] = f"{smtp_config.username}@{smtp_config.host}"
        message["To"] = to
        message["Subject"] = "DOGS Notification (Class Manager Updates)"
        message.set_content(fr"""
Class Manager Has Been Updated:
Class ID: {class_id}
Added CM: {account_id}
Operator: {operator_id}        
""")
        async with smtp_handler.client:
            await smtp_handler.client.send_message(message)
