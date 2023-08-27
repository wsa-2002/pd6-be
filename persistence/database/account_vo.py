from typing import Sequence, Tuple, List

from base import do
from base import enum
from base.popo import Filter, Sorter

from .base import AutoTxConnection, FetchOne, FetchAll
from .util import execute_count, compile_filters, compile_values


async def browse_with_default_student_card(limit: int, offset: int, filters: list[Filter],
                                           sorters: list[Sorter], include_deleted: bool = False) \
        -> tuple[Sequence[Tuple[do.Account, do.StudentCard]], int]:
    if not include_deleted:
        filters.append(Filter(col_name='is_deleted',
                              op=enum.FilterOperator.eq,
                              value=False))

    filters = [Filter(col_name=f'account.{filter_.col_name}',
                      op=filter_.op,
                      value=filter_.value) for filter_ in filters]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"account.{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
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
                fr' ORDER BY {sort_sql} account.id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
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


async def browse_list_with_default_student_card(account_ids: List[int], include_deleted: bool = False) \
        -> Sequence[Tuple[do.Account, do.StudentCard]]:
    cond_sql = ', '.join(str(account_id) for account_id in account_ids)
    async with FetchAll(
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
            raise_not_found=False,  # Issue #134: return [] for browse
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
    async with FetchOne(
            event='read account with default student id',
            sql=fr'SELECT account.id, account.username, account.nickname, account.real_name, account.role,'
                fr'       account.is_deleted, account.alternative_email,'
                fr'       student_card.id, student_card.institute_id, student_card.student_id,'
                fr'       student_card.email, student_card.is_default'
                fr'  FROM account'
                fr'       LEFT JOIN student_card'  # some account might not have student card, so left join
                fr'              ON student_card.account_id = account.id'
                fr'             AND student_card.is_default'
                fr' WHERE account.id = %(account_id)s'
                fr'{" AND NOT account.is_deleted" if not include_deleted else ""}',
            account_id=account_id,
    ) as (account_id, username, nickname, real_name, role, is_deleted, alternative_email,
          student_card_id, institute_id, student_id, email, is_default):
        return (do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                           role=enum.RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                do.StudentCard(id=student_card_id, institute_id=institute_id,
                               student_id=student_id, email=email, is_default=is_default))


async def batch_read_by_account_referral(account_referrals: Sequence[str]) \
        -> Sequence[tuple[do.Account, do.StudentCard]]:
    async with AutoTxConnection(event='batch read account by account referrals') as conn:
        value_sql, value_params = compile_values([
            (account_referral,)
            for account_referral in account_referrals
        ])
        account_ids: list[list[int]] = await conn.fetch(
            fr'  WITH account_referrals (account_referral)'
            fr'    AS (VALUES {value_sql})'
            fr'SELECT account_referral_to_id(account_referral)'
            fr'  FROM account_referrals',
            *value_params,
        )
        value_sql, value_params = compile_values([
            (account_id, )
            for account_id, in account_ids if account_id is not None
        ])
        if not value_sql:
            return []

        records = await conn.fetch(
            fr'SELECT account.id, account.username, account.nickname, account.real_name, account.role,'
            fr'       account.is_deleted, account.alternative_email,'
            fr'       student_card.id, student_card.institute_id, student_card.student_id,'
            fr'       student_card.email, student_card.is_default'
            fr'  FROM account'
            fr'       LEFT JOIN student_card'  # some account might not have student card, so left join
            fr'              ON student_card.account_id = account.id'
            fr'             AND student_card.is_default'
            fr' WHERE account.id IN ({value_sql})',
            *value_params,
        )
        return [(do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                            role=enum.RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                 do.StudentCard(id=student_card_id, institute_id=institute_id,
                                student_id=student_id, email=email, is_default=is_default))
                for
                (account_id, username, nickname, real_name, role, is_deleted, alternative_email, student_card_id,
                 institute_id, student_id, email, is_default) in records]
