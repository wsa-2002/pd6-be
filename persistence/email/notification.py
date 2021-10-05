from email.message import EmailMessage

from config import service_config, smtp_config
from persistence.email import smtp_handler
from typing import Sequence, Collection


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
async def notify_cm_change(tos: Collection[str], class_name: str, course_name: str, operator_account_referral: str,
                           added_account_referrals: Collection[str] = None,
                           removed_account_referrals: Collection[str] = None):
    bccs = ', '.join(tos)
    added_cms = ', '.join(added_account_referrals) or 'None'
    removed_cms = ', '.join(removed_account_referrals) or 'None'
    msg = fr"""
Class Manager Has Been Updated:
Course Name: {course_name}
Class Name: {class_name}
Added CMs: {added_cms}
Removed CMs: {removed_cms}
Operator: {operator_account_referral}      
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
