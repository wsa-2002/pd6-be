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


async def edit_member(class_id: int, member_roles: Sequence[Tuple[int, RoleType]], operator_id: int) -> None:
    cm_before = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_before = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    for member_id, role in member_roles:
        await db.class_.edit_member(class_id=class_id, member_id=member_id, role=role)

    cm_after = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_after = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    class_ = await db.class_.read(class_id=class_id)
    course = await db.course.read(course_id=class_.course_id)
    if cm_before != cm_after:
        added_cms = list(cm_after.difference(cm_before))
        removed_cms = list(cm_before.difference(cm_after))
        class_manager_emails = list(emails_after | emails_before)

        operator = await db.account.read(account_id=operator_id)
        await email.notification.notify_cm_change(tos=class_manager_emails, added_account_referrals=added_cms,
                                                  removed_account_referrals=removed_cms,
                                                  class_name=class_.name, course_name=course.name,
                                                  operator_account_referral=operator.username)


async def replace_members(class_id: int, member_roles: Sequence[Tuple[str, RoleType]], operator_id: int) -> None:
    cm_before = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_before = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    try:
        await db.class_.replace_members(class_id=class_id,
                                        member_roles=[(account_referral, role)
                                                      for (account_referral, role) in member_roles])
    except:
        raise exc.IllegalInput

    cm_after = set(await db.class_.browse_member_referrals(class_id=class_id, role=RoleType.manager))
    emails_after = set(await db.class_.browse_member_emails(class_id=class_id, role=RoleType.manager))

    class_ = await db.class_.read(class_id=class_id)
    course = await db.course.read(course_id=class_.course_id)

    if cm_before != cm_after:
        added_cms = list(cm_after.difference(cm_before))
        removed_cms = list(cm_before.difference(cm_after))
        class_manager_emails = list(emails_after | emails_before)

        operator = await db.account.read(account_id=operator_id)
        await email.notification.notify_cm_change(tos=class_manager_emails, added_account_referrals=added_cms,
                                                  removed_account_referrals=removed_cms,
                                                  class_name=class_.name, course_name=course.name, operator_account_referral=operator.username)
