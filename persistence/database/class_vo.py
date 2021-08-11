from typing import Sequence, Tuple

from base import do
from base.enum import RoleType

from .base import SafeExecutor


async def browse_member_account_with_student_card_and_institute(class_id: int, include_deleted: bool = False) \
        -> Sequence[Tuple[do.ClassMember, do.Account, do.StudentCard, do.Institute]]:
    async with SafeExecutor(
            event='browse class members with student card',
            sql=fr'SELECT class_member.member_id, class_member.class_id, class_member.role,'
                fr'       account.id, account.username, account.nickname, account.real_name, account.role,'
                fr'       account.is_deleted, account.alternative_email,'
                fr'       student_card.id, student_card.institute_id, student_card.student_id,'
                fr'       student_card.email, student_card.is_default,'
                fr'       institute.id, institute.abbreviated_name, institute.full_name,'
                fr'       institute.email_domain, institute.is_disabled'
                fr'  FROM class_member'
                fr' INNER JOIN account'
                fr'         ON class_member.member_id = account.id'
                fr'{f"     AND NOT account.is_deleted" if include_deleted else ""}'
                fr'  LEFT JOIN student_card'  # some account might not have student card, so left join
                fr'         ON account.id = student_card.account_id'
                fr'        AND student_card.is_default'
                fr' INNER JOIN institute'
                fr'         ON student_card.institute_id = institute.id'
                fr' WHERE class_member.class_id = %(class_id)s',
            class_id=class_id,
            fetch='all',
    ) as records:
        return [(do.ClassMember(member_id=member_id, class_id=class_id, role=RoleType(role)),
                 do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                            role=RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                 do.StudentCard(id=student_card_id, institute_id=institute_id,
                                student_id=student_id, email=email, is_default=is_default),
                 do.Institute(id=institute_id, abbreviated_name=abbreviated_name, full_name=full_name,
                              email_domain=email_domain, is_disabled=is_disabled))
                for (member_id, class_id, role,
                     account_id, username, nickname, real_name, role, is_deleted, alternative_email,
                     student_card_id, institute_id, student_id, email, is_default,
                     institute_id, abbreviated_name, full_name, email_domain, is_disabled)
                in records]
