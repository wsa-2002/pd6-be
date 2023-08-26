from typing import Sequence, Tuple

from base import do
from base.enum import RoleType, SortOrder
from base.popo import Filter, Sorter

from .base import FetchAll
from .util import execute_count, compile_filters


async def browse_member_account_with_student_card_and_institute(
        limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter], include_deleted: bool = False) \
        -> tuple[Sequence[Tuple[do.ClassMember, do.Account, do.StudentCard, do.Institute]], int]:

    filters = [Filter(col_name=f'class_member.{filter_.col_name}',
                      op=filter_.op,
                      value=filter_.value) for filter_ in filters]

    sorters += [Sorter(col_name='role',
                       order=SortOrder.desc)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"class_member.{sorter.col_name} {sorter.order}" for sorter in sorters)

    async with FetchAll(
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
                fr'{"      AND NOT account.is_deleted" if not include_deleted else ""}'
                fr'  LEFT JOIN student_card'  # some account might not have student card, so left join
                fr'         ON account.id = student_card.account_id'
                fr'        AND student_card.is_default'
                fr'  LEFT JOIN institute'
                fr'         ON student_card.institute_id = institute.id'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY{f" {sort_sql}," if sort_sql else ""} class_member.member_id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [(do.ClassMember(member_id=member_id, class_id=class_id, role=RoleType(class_role)),
                 do.Account(id=account_id, username=username, nickname=nickname, real_name=real_name,
                            role=RoleType(role), is_deleted=is_deleted, alternative_email=alternative_email),
                 do.StudentCard(id=student_card_id, institute_id=institute_id,
                                student_id=student_id, email=email, is_default=is_default),
                 do.Institute(id=institute_id, abbreviated_name=abbreviated_name, full_name=full_name,
                              email_domain=email_domain, is_disabled=is_disabled))
                for (member_id, class_id, class_role,
                     account_id, username, nickname, real_name, role, is_deleted, alternative_email,
                     student_card_id, institute_id, student_id, email, is_default,
                     institute_id, abbreviated_name, full_name, email_domain, is_disabled)
                in records]

    total_count = await execute_count(
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
            fr'{"      AND NOT account.is_deleted" if not include_deleted else ""}'
            fr'  LEFT JOIN student_card'  # some account might not have student card, so left join
            fr'         ON account.id = student_card.account_id'
            fr'        AND student_card.is_default'
            fr'  LEFT JOIN institute'
            fr'         ON student_card.institute_id = institute.id'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )
    return data, total_count


async def browse_class_member_with_account_id(class_id: int, include_deleted: bool = False) \
        -> Sequence[Tuple[do.ClassMember, int]]:
    async with FetchAll(
            event='browse class members with account id',
            sql=fr'SELECT class_member.member_id, class_member.class_id, class_member.role, '
                fr'       account.id'
                fr'  FROM class_member'
                fr' INNER JOIN account'
                fr'         ON class_member.member_id = account.id'
                fr'{"     AND NOT account.is_deleted" if not include_deleted else ""}'
                fr' WHERE class_member.class_id = %(class_id)s',
            class_id=class_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [(do.ClassMember(member_id=member_id, class_id=class_id, role=RoleType(role_str)), account_id)
                for (member_id, class_id, role_str, account_id) in records]


async def browse_class_member_with_account_referral(class_id: int, include_deleted: bool = False) \
        -> Sequence[Tuple[do.ClassMember, str]]:
    async with FetchAll(
            event='browse class members with account referral',
            sql=fr'SELECT class_member.member_id, class_member.class_id, class_member.role, '
                fr'       account_id_to_referral(class_member.member_id)'
                fr'  FROM class_member'
                fr' INNER JOIN account'
                fr'         ON class_member.member_id = account.id'
                fr' WHERE class_member.class_id = %(class_id)s'
                fr'{" AND NOT account.is_deleted" if not include_deleted else ""}',
            class_id=class_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [(do.ClassMember(member_id=member_id, class_id=class_id, role=RoleType(role_str)), account_referral)
                for (member_id, class_id, role_str, account_referral) in records]
