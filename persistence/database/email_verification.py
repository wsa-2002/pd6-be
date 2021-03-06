from typing import Sequence

from base import do

from .base import FetchAll, FetchOne, OnlyExecute


async def browse(account_id: int, is_consumed=False) -> Sequence[do.EmailVerification]:
    async with FetchAll(
            event='browse account pending email verification',
            sql=fr'SELECT id, account_id, institute_id, student_id, email, is_consumed'
                fr'  FROM email_verification'
                fr' WHERE account_id = %(account_id)s'
                fr'   AND is_consumed = %(is_consumed)s'
                fr' ORDER BY id ASC',
            account_id=account_id, is_consumed=is_consumed,
            raise_not_found=False,
    ) as record:
        return [do.EmailVerification(id=id_, account_id=account_id, institute_id=institute_id, student_id=student_id,
                                     email=email, is_consumed=is_consumed)
                for (id_, account_id, institute_id, student_id, email, is_consumed) in record]


async def read(email_verification_id: int) -> do.EmailVerification:
    async with FetchOne(
            event='read email verification',
            sql=fr'SELECT id, account_id, institute_id, student_id, email, is_consumed'
                fr'  FROM email_verification'
                fr' WHERE id = %(email_verification_id)s',
            email_verification_id=email_verification_id,
    ) as (id_, account_id, institute_id, student_id, email, is_consumed):
        return do.EmailVerification(id=id_, account_id=account_id, institute_id=institute_id, student_id=student_id,
                                    email=email, is_consumed=is_consumed)


async def read_verification_code(email_verification_id: int) -> str:
    async with FetchOne(
            event='get verification code',
            sql=fr'SELECT code'
                fr'  FROM email_verification'
                fr' WHERE id = %(email_verification_id)s',
            email_verification_id=email_verification_id,
    ) as (code,):
        return code


async def delete(email_verification_id: int) -> None:
    async with OnlyExecute(
            event='HARD delete email verification',
            sql=fr'DELETE FROM email_verification'
                fr' WHERE id = %(email_verification_id)s',
            email_verification_id=email_verification_id,
    ):
        pass
