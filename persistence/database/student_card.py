from typing import Sequence

from base import do

from .base import SafeExecutor


async def add(account_id: int, institute_id: int, department: str, student_id: str, email: str, is_deleted: bool) \
        -> int:
    async with SafeExecutor(
            event='Add student card',
            sql=r'INSERT INTO student_card'
                r'            (account_id, institute_id, department, student_id, email, is_deleted)'
                r'     VALUES (%(account_id)s, %(institute_id)s, %(department)s, %(student_id)s, %(email)s,'
                r'             %(is_deleted)s)'
                r'  RETURNING id',
            account_id=account_id,
            institute_id=institute_id,
            department=department,
            student_id=student_id,
            email=email,
            is_deleted=is_deleted,
            fetch=1,
    ) as (id_,):
        return id_


async def read(student_card_id: int, *, include_deleted: bool = False) -> do.StudentCard:
    async with SafeExecutor(
            event='get student card by id',
            sql=fr'SELECT id, institute_id, department, student_id, email, is_deleted'
                fr'  FROM student_card'
                fr' WHERE id = %(student_card)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            student_card=student_card_id,
            fetch=1,
    ) as (id_, institute_id, department, student_id, email, is_deleted):
        return do.StudentCard(id=id_, institute_id=institute_id, department=department, student_id=student_id,
                              email=email, is_deleted=is_deleted)


async def browse(account_id: int, *, include_deleted: bool = False) -> Sequence[do.StudentCard]:
    async with SafeExecutor(
            event='browse student card by account id',
            sql=fr'SELECT student_card.id, institute_id, department, student_id, email, is_deleted'
                fr'  FROM student_card, account_student_card'
                fr' WHERE student_card.id = account_student_card.student_card_id'
                fr'   AND account_student_card.account_id = %(account_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            account_id=account_id,
            fetch='all',
    ) as records:
        return [do.StudentCard(id=id_, institute_id=institute_id, department=department, student_id=student_id,
                               email=email, is_deleted=is_deleted)
                for (id_, institute_id, department, student_id, email, is_deleted) in records]


async def read_owner_id(student_card_id: int, *, include_deleted: bool = False) -> int:
    async with SafeExecutor(
            event='get student owner id by student card id',
            sql=fr'SELECT account_id'
                fr'  FROM account_student_card'
                fr' WHERE account_student_card.student_card_id = %(student_card_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            student_card_id=student_card_id,
            fetch=1,
    ) as (id_,):
        return id_


async def edit(student_card_id: int,
               institute_id: int = None, department: str = None, student_id: str = None, email: str = None,
               is_enabled: bool = None) -> None:
    to_updates = {}

    if institute_id is not None:
        to_updates['institute_id'] = institute_id
    if department is not None:
        to_updates['department'] = department
    if student_id is not None:
        to_updates['student_id'] = student_id
    if email is not None:
        to_updates['email'] = email
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit student_card by id',
            sql=fr'UPDATE student_card'
                fr' WHERE student_card.id = %(student_card_id)s'
                fr'   SET {set_sql}',
            student_card_id=student_card_id,
            **to_updates,
    ):
        pass


async def delete(student_card_id: int) -> None:
    async with SafeExecutor(
            event='soft delete student_card',
            sql=fr'UPDATE student_card'
                fr' WHERE student_card.id = %(student_card_id)s'
                fr'   SET is_deleted = %(is_deleted)s',
            student_card_id=student_card_id,
            is_deleted=True,
    ):
        return
