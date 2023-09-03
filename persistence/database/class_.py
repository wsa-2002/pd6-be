from itertools import chain
from operator import itemgetter
from typing import Sequence, Collection, Tuple

import log
from base import do
from base.enum import RoleType, FilterOperator
from base.popo import Filter, Sorter

from . import team, challenge
from .base import AutoTxConnection, FetchAll, FetchOne, OnlyExecute, ParamDict
from .util import execute_count, compile_filters, compile_values


async def add(name: str, course_id: int) -> int:
    async with FetchOne(
            event='add class',
            sql=r'INSERT INTO class'
                r'            (name, course_id)'
                r'     VALUES (%(name)s, %(course_id)s)'
                r'  RETURNING id',
            name=name,
            course_id=course_id,
    ) as (course_id,):
        return course_id


async def browse(course_id: int = None, include_deleted=False) -> Sequence[do.Class]:
    conditions: ParamDict = {}
    if course_id is not None:
        conditions['course_id'] = course_id

    filters = []
    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(list(fr"{field_name} = %({field_name})s" for field_name in conditions)
                            + filters)

    async with FetchAll(
            event='browse classes',
            sql=fr'SELECT id, name, course_id, is_deleted'
                fr'  FROM class'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY course_id ASC, name DESC, id ASC',
            **conditions,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Class(id=id_, name=name, course_id=course_id, is_deleted=is_deleted)
                for (id_, name, course_id, is_deleted) in records]


async def browse_with_filter(limit: int, offset: int, filters: Sequence[Filter], sorters: Sequence[Sorter],
                             course_id: int = None, include_deleted=False) -> tuple[Sequence[do.Class], int]:
    if course_id is not None:
        filters += [Filter(col_name='course_id',
                           op=FilterOperator.eq,
                           value=course_id)]

    if not include_deleted:
        filters += [Filter(col_name='is_deleted',
                           op=FilterOperator.eq,
                           value=include_deleted)]

    cond_sql, cond_params = compile_filters(filters)
    sort_sql = ' ,'.join(f"{sorter.col_name} {sorter.order}" for sorter in sorters)
    if sort_sql:
        sort_sql += ','

    async with FetchAll(
            event='browse classes',
            sql=fr'SELECT id, name, course_id, is_deleted'
                fr'  FROM class'
                fr'{f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY {sort_sql} course_id ASC, id ASC'
                fr' LIMIT %(limit)s OFFSET %(offset)s',
            **cond_params,
            limit=limit, offset=offset,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        data = [do.Class(id=id_, name=name, course_id=course_id, is_deleted=is_deleted)
                for (id_, name, course_id, is_deleted) in records]

    total_count = await execute_count(
        sql=fr'SELECT id, name, course_id, is_deleted'
            fr'  FROM class'
            fr'{f" WHERE {cond_sql}" if cond_sql else ""}',
        **cond_params,
    )

    return data, total_count


async def browse_from_member_role(member_id: int, role: RoleType, include_deleted=False) \
        -> Sequence[do.Class]:
    async with FetchAll(
            event='browse classes from account role',
            sql=fr'SELECT class.id, class.name, class.course_id, class.is_deleted'
                fr'  FROM class'
                fr'       INNER JOIN class_member'
                fr'               ON class_member.class_id = class.id'
                fr'              AND class_member.member_id = %(member_id)s'
                fr' WHERE class_member.role = %(role)s'
                fr'{" AND NOT class.is_deleted" if not include_deleted else ""}'
                fr' ORDER BY class.course_id ASC, class.id ASC',
            role=role,
            member_id=member_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Class(id=id_, name=name, course_id=course_id, is_deleted=is_deleted)
                for (id_, name, course_id, is_deleted) in records]


async def read(class_id: int, *, include_deleted=False) -> do.Class:
    async with FetchOne(
            event='read class by id',
            sql=fr'SELECT id, name, course_id, is_deleted'
                fr'  FROM class'
                fr' WHERE id = %(class_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            class_id=class_id,
    ) as (id_, name, course_id, is_deleted):
        return do.Class(id=id_, name=name, course_id=course_id, is_deleted=is_deleted)


async def edit(class_id: int, name: str = None, course_id: int = None):
    to_updates: ParamDict = {}

    if name is not None:
        to_updates['name'] = name
    if course_id is not None:
        to_updates['course_id'] = course_id

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='edit class by id',
            sql=fr'UPDATE class'
                fr'   SET {set_sql}'
                fr' WHERE id = %(class_id)s',
            class_id=class_id,
            **to_updates,
    ):
        pass


async def delete(class_id: int) -> None:
    async with OnlyExecute(
            event='soft delete class',
            sql=r'UPDATE class'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(class_id)s',
            class_id=class_id,
            is_deleted=True,
    ):
        pass


async def delete_cascade(class_id: int) -> None:
    async with AutoTxConnection(event=f'cascade delete from class {class_id=}') as conn:
        await team.delete_cascade_from_class(class_id=class_id, cascading_conn=conn)
        await challenge.delete_cascade_from_class(class_id=class_id, cascading_conn=conn)

        await conn.execute(r'UPDATE class'
                           r'   SET is_deleted = $1'
                           r' WHERE id = $2',
                           True, class_id)


async def delete_cascade_from_course(course_id: int, cascading_conn=None) -> None:
    if cascading_conn:
        await _delete_cascade_from_course(course_id, conn=cascading_conn)
        return

    async with AutoTxConnection(event=f'cascade delete class from course {course_id=}') as conn:
        await _delete_cascade_from_course(course_id, conn=conn)


async def _delete_cascade_from_course(course_id: int, conn) -> None:
    await conn.execute(r'UPDATE class'
                       r'   SET is_deleted = $1'
                       r' WHERE course_id = $2',
                       True, course_id)


# === member control


async def add_member(class_id: int, member_id: int, role: RoleType):
    async with OnlyExecute(
            event='add member to class',
            sql=r'INSERT INTO class_member'
                r'            (class_id, member_id, role)'
                r'     VALUES (%(class_id)s, %(member_id)s, %(role)s)',
            class_id=class_id,
            member_id=member_id,
            role=role,
    ):
        pass


async def add_members(class_id: int, member_roles: Collection[Tuple[int, RoleType]]):
    async with AutoTxConnection(event='add members to class') as conn:
        await conn.executemany(
            command=r'INSERT INTO class_member'
                    r'            (class_id, member_id, role)'
                    r'     VALUES ($1, $2, $3)',
            args=[(class_id, member_id, role)
                  for member_id, role in member_roles],
        )


async def browse_role_by_account_id(account_id: int) \
        -> Sequence[Tuple[do.ClassMember, do.Class, do.Course]]:
    async with FetchAll(
            event='browse class role by account_id',
            sql=r'SELECT class_member.class_id, class_member.member_id, class_member.role,'
                r'       class.id, class.name, class.course_id, class.is_deleted,'
                r'       course.id, course.name, course.type, course.is_deleted'
                r' FROM class_member'
                r' INNER JOIN class'
                r'         ON class.id = class_member.class_id'
                r'        AND class.is_deleted = %(class_is_deleted)s'
                r' INNER JOIN course'
                r'         ON course.id = class.course_id'
                r'        AND course.is_deleted = %(course_is_deleted)s'
                r' WHERE class_member.member_id = %(account_id)s',
            account_id=account_id, class_is_deleted=False, course_is_deleted=False,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [(do.ClassMember(class_id=class_id, member_id=member_id, role=RoleType(role)),
                 do.Class(id=class_id, name=class_name, course_id=course_id, is_deleted=is_deleted),
                 do.Course(id=course_id, name=course_name, type=type_, is_deleted=is_deleted))
                for (class_id, member_id, role,
                     class_id, class_name, course_id, is_deleted,
                     course_id, course_name, type_, is_deleted) in records]


async def browse_members(class_id: int) -> Sequence[do.ClassMember]:
    async with FetchAll(
            event='browse class members',
            sql=r'SELECT account.id, class_member.class_id, class_member.role'
                r'  FROM class_member, account'
                r' WHERE class_member.member_id = account.id'
                r'   AND class_member.class_id = %(class_id)s'
                r' ORDER BY class_member.role DESC, account.id ASC',
            class_id=class_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.ClassMember(member_id=id_, class_id=class_id, role=RoleType(role_str))
                for id_, class_id, role_str in records]


async def get_member_counts(class_ids: list[int]) -> list[int]:
    if not class_ids:
        return []

    kwargs = {f'class_id_{i}': class_id for i, class_id in enumerate(class_ids, start=1)}
    to_selects = [f'COUNT(*) FILTER (WHERE class_member.class_id = %({kw})s)' for kw in kwargs]

    async with FetchOne(
            event='get class member counts',
            sql=fr'SELECT {", ".join(to_selects)}'
                fr'  FROM class_member',
            **kwargs,
    ) as counts:
        return list(counts)


async def read_member(class_id: int, member_id: int) -> do.ClassMember:
    async with FetchOne(
            event='read class member role',
            sql=r'SELECT member_id, class_id, role'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s and member_id = %(member_id)s',
            class_id=class_id,
            member_id=member_id,
    ) as (member_id, class_id, role):
        return do.ClassMember(member_id=member_id, class_id=class_id, role=RoleType(role))


async def delete_member(class_id: int, member_id: int):
    async with OnlyExecute(
            event='HARD DELETE class member',
            sql=r'DELETE FROM class_member'
                r'      WHERE class_id = %(class_id)s AND member_id = %(member_id)s',
            class_id=class_id,
            member_id=member_id,
    ):
        pass


async def browse_member_emails(class_id: int, role: RoleType = None) -> Sequence[str]:
    conditions: ParamDict = {}
    if role is not None:
        conditions['role'] = role

    async with FetchAll(
            event='browse class member emails',
            sql=fr'SELECT student_card.email'
                fr'  FROM class_member, student_card'
                fr' WHERE class_member.member_id = student_card.account_id'
                fr'   AND student_card.is_default = true'
                fr'   AND class_member.class_id = %(class_id)s'
                fr' {"AND class_member.role = %(role)s" if role is not None else ""}',
            class_id=class_id,
            **conditions,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [institute_email for institute_email, in records]


async def replace_members(class_id: int, member_roles: Sequence[Tuple[str, RoleType]]) -> Sequence[bool]:
    """
    :return: a list of bool indicating if the insertion is successful (true) or not (false)
    """
    if not member_roles:
        async with OnlyExecute(
                event=f'remove all members from class {class_id=}',
                sql=r'DELETE FROM class_member'
                    r'      WHERE class_id = %(class_id)s',
                class_id=class_id,
        ):
            log.info('Removed all class members')
            return []

    async with AutoTxConnection(event=f'replace members from class {class_id=}') as conn:
        # 1. get the referrals
        value_sql, value_params = compile_values([
            (account_referral,)
            for account_referral, _ in member_roles
        ])
        log.info(f'Fetching account ids with values {value_params}')
        account_ids: list[list[int]] = await conn.fetch(
            fr'  WITH account_referrals (account_referral)'
            fr'    AS (VALUES {value_sql})'
            fr'SELECT account_referral_to_id(account_referral)'
            fr'  FROM account_referrals',
            *value_params,
        )
        log.info(f'Fetched account ids: {account_ids}')

        # 2. remove the old members
        await conn.execute(r'DELETE FROM class_member'
                           r'      WHERE class_id = $1',
                           class_id)
        log.info('Removed old class members')

        # 3. perform insert
        value_sql, value_params = compile_values(sorted((
            (class_id, account_id, role)
            for (account_id,), (_, role) in zip(account_ids, member_roles)
            if account_id is not None
        ), key=itemgetter(2), reverse=True))
        log.info(f'Inserting new class members with values {value_params}')
        inserted_account_ids: list[list[int]] = await conn.fetch(
            fr' INSERT INTO class_member'
            fr'             (class_id, member_id, role)'
            fr'      VALUES {value_sql}'
            fr' ON CONFLICT DO NOTHING'
            fr'   RETURNING member_id',
            *value_params,
        )
        log.info(f'Inserted {len(inserted_account_ids)} out of {len(account_ids)} given new class members')

    # 4. check the failed account ids
    success_account_ids = set(chain(*inserted_account_ids))
    return [account_id in success_account_ids for account_id in chain(*account_ids)]


async def browse_member_referrals(class_id: int, role: RoleType) -> Sequence[str]:
    async with FetchAll(
            event='get member account referral by role',
            sql=r'SELECT account_id_to_referral(member_id)'
                r'  FROM class_member'
                r' WHERE class_id = %(class_id)s'
                r'   AND role = %(role)s',
            class_id=class_id, role=role,
            raise_not_found=False,
    ) as records:
        return [referral for referral, in records]
