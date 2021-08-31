from email.message import EmailMessage

from config import service_config, smtp_config
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
async def notify_cm_change(tos: Sequence[str], class_id: int, operator_id: int,
                           added_account_ids: Sequence[int] = None,
                           removed_account_ids: Sequence[int] = None):
    bccs = ', '.join(tos)
    msg = fr"""
Class Manager Has Been Updated:
Class ID: {class_id}
{f"Added CMs: {', '.join(str(account_id) for account_id in added_account_ids)}" if added_account_ids else ""}
{f"Removed CMs: {', '.join(str(account_id) for account_id in removed_account_ids)}" if removed_account_ids else ""}
Operator: {operator_id}        
"""
    subject = "PDOGS Notification (Class Manager Updates)"
    await send(bcc=bccs, msg=msg, subject=subject)


# send file download url
async def send_file_download_url(to: str, file_url: str, subject='PDOGS File Download URL'):
    message = EmailMessage()
    message["From"] = f"{smtp_config.username}@{smtp_config.host}"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(fr"""
Please download your file with the following url:
{file_url}
""")

    async with smtp_handler.client:
        await smtp_handler.client.send_message(message)
