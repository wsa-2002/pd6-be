from typing import Sequence

from base import vo
from base.enum import RoleType

from .base import SafeExecutor


async def browse_members_with_student_card(class_id: int) -> Sequence[vo.MemberWithStudentCard]:
    async with SafeExecutor(
            event='browse class members with student card',
            sql=fr'SELECT account.id, account.username, account.real_name,'
                fr'       institute.abbreviated_name,'
                fr'       student_card.student_id, class_member.role'
                fr'  FROM account, institute, student_card, class_member'
                fr' WHERE class_member.member_id = account.id'
                fr'   AND class_member.class_id = %(class_id)s'
                fr'   AND student_card.account_id = account.id'
                fr'   AND student_card.institute_id = institute.id'
                fr'   AND student_card.is_default = %(is_default)s',
            class_id=class_id,
            is_default=True,
            fetch='all',
    ) as records:
        return [vo.MemberWithStudentCard(id=id_, username=username, student_id=student_id, real_name=real_name,
                                         institute=institute, role=RoleType(role_str))
                for id_, username, real_name, institute, student_id, role_str in records]
