import persistence.database as db
import persistence.email as email


async def add(account_id: int, institute_email: str, institute_id: int, student_id: str):
    code = await db.account.add_email_verification(email=institute_email, account_id=account_id,
                                                   institute_id=institute_id, department='',
                                                   student_id=student_id)
    await email.verification.send(to=institute_email, code=code)


browse = db.student_card.browse
read = db.student_card.read
read_owner_id = db.student_card.read_owner_id

is_duplicate = db.student_card.is_duplicate
