from typing import Sequence, Tuple, List

from base import do
from base import enum

from .base import SafeExecutor


async def browse_with_default_student_card(include_deleted: bool = False) \
        -> Sequence[Tuple[do.Account, do.StudentCard]]:
    async with SafeExecutor(
            event='browse account with default student id',
            sql=fr'SELECT account.id, account.username, account.nickname, account.real_name, account.role,'
                fr'       account.is_deleted, account.alternative_email,'
                fr'       student_card.id, student_card.institute_id, student_card.student_id,'
                fr'       student_card.email, student_card.is_default'
                fr'  FROM account'
                fr'       LEFT JOIN student_card'  # some account might not have student card, so left join
                fr'              ON student_card.account_id = account.id'
                fr'             AND student_card.is_default'
                fr'{" WHERE NOT account.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY account.id ASC',
            fetch='all',
    ) as records:
        return [(do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                            role=enum.RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                 do.StudentCard(id=student_card_id, institute_id=institute_id,
                                student_id=student_id, email=email, is_default=is_default))
                for (account_id, username, nickname, real_name, role, is_deleted, alternative_email,
                     student_card_id, institute_id, student_id, email, is_default)
                in records]


async def browse_list_with_default_student_card(account_ids: List[int], include_deleted: bool = False) \
        -> Sequence[Tuple[do.Account, do.StudentCard]]:
    cond_sql = ', '.join(str(account_id) for account_id in account_ids)
    async with SafeExecutor(
            event='browse account with default student id',
            sql=fr'SELECT account.id, account.username, account.nickname, account.real_name, account.role,'
                fr'       account.is_deleted, account.alternative_email,'
                fr'       student_card.id, student_card.institute_id, student_card.student_id,'
                fr'       student_card.email, student_card.is_default'
                fr'  FROM account'
                fr'       LEFT JOIN student_card'  # some account might not have student card, so left join
                fr'              ON student_card.account_id = account.id'
                fr'             AND student_card.is_default'
                fr'{" WHERE NOT account.is_deleted" if not include_deleted else ""}'
                fr'         AND account.id IN ({cond_sql})',
            fetch='all',
    ) as records:
        return [(do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                            role=enum.RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                 do.StudentCard(id=student_card_id, institute_id=institute_id,
                                student_id=student_id, email=email, is_default=is_default))
                for (account_id, username, nickname, real_name, role, is_deleted, alternative_email,
                     student_card_id, institute_id, student_id, email, is_default)
                in records]


async def read_with_default_student_card(account_id: int, include_deleted: bool = False) \
        -> Tuple[do.Account, do.StudentCard]:
    async with SafeExecutor(
            event='read account with default student id',
            sql=fr'SELECT account.id, account.username, account.nickname, account.real_name, account.role,'
                fr'       account.is_deleted, account.alternative_email,'
                fr'       student_card.id, student_card.institute_id, student_card.student_id,'
                fr'       student_card.email, student_card.is_default'
                fr'  FROM account'
                fr'       LEFT JOIN student_card'  # some account might not have student card, so left join
                fr'              ON student_card.account_id = %(account_id)s'
                fr'             AND student_card.is_default'
                fr' WHERE account.id = %(account_id)s'
                fr'{" AND NOT account.is_deleted" if not include_deleted else ""}',
            account_id=account_id,
            fetch=1,
    ) as (account_id, username, nickname, real_name, role, is_deleted, alternative_email,
          student_card_id, institute_id, student_id, email, is_default):
        return (do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                           role=enum.RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                do.StudentCard(id=student_card_id, institute_id=institute_id,
                               student_id=student_id, email=email, is_default=is_default))

