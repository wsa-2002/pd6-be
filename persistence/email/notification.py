from email.message import EmailMessage

from config import smtp_config
from persistence.email import smtp_handler
from typing import Sequence


# for general msgs
async def send(to: str = None, msg: str = "", bcc: str = None, subject='PDOGS Notification'):
    message = EmailMessage()
    message["From"] = f"{smtp_config.username}@{smtp_config.host}"
    if to is not None:
        message["To"] = to
    if bcc is not None:
        message["Bcc"] = bcc
    message["Subject"] = subject
    message.set_content(msg)

    async with smtp_handler.client:
        await smtp_handler.client.send_message(message)


# update class manager change
async def notify_cm_change(tos: Sequence[str], account_id: int, class_id: int, operator_id: int):
    bccs = ', '.join(tos)
    msg = fr"""
Class Manager Has Been Updated:
Class ID: {class_id}
Added CM: {account_id}
Operator: {operator_id}        
"""
    subject = "PDOGS Notification (Class Manager Updates)"
    await send(bcc=bccs, msg=msg, subject=subject)
