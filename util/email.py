from persistence import database as db
import re


def is_valid_email(email: str) -> bool:
    regex = r"^[-!#$%&'*+/0-9=?A-Z^_a-z{|}~](\.?[-!#$%&'*+/0-9=?A-Z^_a-z{|}~])*@[a-zA-Z](-?[a-zA-Z0-9])*(\.[a-zA-Z](-?[a-zA-Z0-9])*)+$"
    if(re.match(regex, email)):
        return True
    return False

async def verify_email(institute_email: str, institute_id: int, student_id: str) -> bool:
    try:
        # check student_id
        if institute_email.split('@')[0] != student_id:
            return False
        
        institute = await db.institute.read(institute_id)
        # check disabled institute
        if institute.is_disabled:
            return False
        
        # check domain
        if institute.email_domain != institute_email.split('@')[1]:
            return False

        return True
        
    except:
        return False
