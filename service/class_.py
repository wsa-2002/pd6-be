from typing import Sequence, Tuple

from base.enum import RoleType
import exceptions as exc
import persistence.database as db
import persistence.email as email

add = db.class_.add
edit = db.class_.edit
browse = db.class_.browse
browse_with_filter = db.class_.browse_with_filter
read = db.class_.read
delete = db.class_.delete_cascade

add_members = db.class_.add_members
browse_member_account_with_student_card_and_institute = db.class_vo.browse_member_account_with_student_card_and_institute
browse_class_member_with_account_id = db.class_vo.browse_class_member_with_account_id
browse_class_member_with_account_referral = db.class_vo.browse_class_member_with_account_referral
delete_member = db.class_.delete_member


async def replace_members(class_id: int, member_roles: Sequence[Tuple[str, RoleType]], operator_id: int) \
        -> Sequence[bool]:
    cm_before = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_before = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    result = await db.class_.replace_members(class_id=class_id, member_roles=member_roles)

    cm_after = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_after = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    if cm_before != cm_after:
        await email.notification.notify_cm_change(
            tos=(emails_after | emails_before),
            added_account_referrals=cm_after.difference(cm_before),
            removed_account_referrals=cm_before.difference(cm_after),
            class_name=(await db.class_.read(class_id=class_id)).name,
            course_name=(await db.course.read(course_id=class_.course_id)).name,
            operator_account_referral=(await db.account.read(account_id=operator_id)).username,
        )

    return result
