from persistence import database as db
import re


email_regex = re.compile(r"^[-!#$%&'*+/0-9=?A-Z^_a-z{|}~](\.?[-!#$%&'*+/0-9=?A-Z^_a-z{|}~])*@[a-zA-Z](-?[a-zA-Z0-9])*(\.[a-zA-Z](-?[a-zA-Z0-9])*)+$")


def is_valid_email(email: str) -> bool:
    if email_regex.match(email):
        return True
    return False


async def verify_institute_email(institute_email: str, institute_id: int, student_id: str) -> bool:
    email_username, email_domain = institute_email.split('@')

    if email_username != student_id:
        return False
    
    institute = await db.institute.read(institute_id, include_disabled=False)

    if email_domain != institute.email_domain:
        return False
    
    return True
