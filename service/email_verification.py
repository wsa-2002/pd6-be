import persistence.database as db
import persistence.email as email

browse = db.email_verification.browse
read = db.email_verification.read
delete = db.email_verification.delete


async def resend(email_verification_id: int):
    email_verification = await db.email_verification.read(email_verification_id)
    code = await db.email_verification.read_verification_code(email_verification_id)
    await email.verification.send(to=email_verification.email, code=code)
