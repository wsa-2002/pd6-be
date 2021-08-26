from typing import Sequence, Tuple

from base import do
from base import enum
from base.popo import Filter, Sorter

from .base import SafeExecutor
from .util import execute_count, compile_filters


async def browse_with_default_student_card(limit: int, offset: int, filters: Sequence[Filter],
                                           sorters: Sequence[Sorter], include_deleted: bool = False) \
        -> tuple[Sequence[Tuple[do.Account, do.StudentCard]], int]:

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"account.{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

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
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr'{" AND NOT account.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY {sort_sql} account.id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            fetch='all',
            raise_not_found=False,
    ) as records:
        data = [(do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                            role=enum.RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                 do.StudentCard(id=student_card_id, institute_id=institute_id,
                                student_id=student_id, email=email, is_default=is_default))
                for (account_id, username, nickname, real_name, role, is_deleted, alternative_email,
                     student_card_id, institute_id, student_id, email, is_default)
                in records]

    total_count = await execute_count(
        sql=fr'SELECT id, username, nickname, real_name, role, is_deleted, alternative_email'
            fr'  FROM account'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


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