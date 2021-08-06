from typing import Sequence

from base import vo

from .base import SafeExecutor


async def browse_account_with_default_student_id(include_deleted: bool = False) -> Sequence[vo.AccountWithStudentId]:
    async with SafeExecutor(
            event='browse account',
            sql=fr'SELECT account.id, student_card.student_id, account.real_name,'
                fr'       account.username, account.nickname, account.alternative_email'
                fr'  FROM account'
                fr'       INNER JOIN student_card'
                fr'               ON student_card.account_id = account.id'
                fr' WHERE student_card.is_default'
                fr'{" AND NOT account.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY account.id ASC',
            fetch='all',
    ) as records:
        return [vo.AccountWithStudentId(id=id_, student_id=student_id, real_name=real_name,
                                        username=username, nickname=nickname, alternative_email=alternative_email)
                for (id_, student_id, real_name, username, nickname, alternative_email)
                in records]
