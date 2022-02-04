from typing import Sequence

from base import do

from .base import FetchOne, FetchAll, OnlyExecute, ParamDict


async def add(abbreviated_name: str, full_name: str, email_domain: str, is_disabled: bool) -> int:
    async with FetchOne(
            event='Add institute',
            sql=r'INSERT INTO institute'
                r'            (abbreviated_name, full_name, email_domain, is_disabled)'
                r'     VALUES (%(abbreviated_name)s, %(full_name)s, %(email_domain)s, %(is_disabled)s)'
                r'  RETURNING id',
            abbreviated_name=abbreviated_name,
            full_name=full_name,
            email_domain=email_domain,
            is_disabled=is_disabled,
    ) as (institute_id,):
        return institute_id


async def browse(*, include_disabled=True) -> Sequence[do.Institute]:
    async with FetchAll(
            event='get all institutes',
            sql=fr'SELECT id, abbreviated_name, full_name, email_domain, is_disabled'
                fr'  FROM institute'
                fr'{" WHERE NOT is_disabled" if not include_disabled else ""}'
                fr' ORDER BY id ASC',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Institute(id=id_, abbreviated_name=abbreviated_name, full_name=full_name, email_domain=email_domain,
                             is_disabled=is_disabled)
                for (id_, abbreviated_name, full_name, email_domain, is_disabled) in records]


async def read(institute_id: int, *, include_disabled=True) -> do.Institute:
    async with FetchOne(
            event='get all institutes',
            sql=fr'SELECT id, abbreviated_name, full_name, email_domain, is_disabled'
                fr'  FROM institute'
                fr' WHERE id = %(institute_id)s'
                fr'{" AND NOT is_disabled" if not include_disabled else ""}'
                fr' ORDER BY id',
            institute_id=institute_id,
    ) as (id_, abbreviated_name, full_name, email_domain, is_disabled):
        return do.Institute(id=id_, abbreviated_name=abbreviated_name, full_name=full_name, email_domain=email_domain,
                            is_disabled=is_disabled)


async def edit(institute_id: int, abbreviated_name: str = None, full_name: str = None, email_domain: str = None,
               is_disabled: bool = None) -> None:
    to_updates: ParamDict = {}

    if abbreviated_name:
        to_updates['abbreviated_name'] = abbreviated_name
    if full_name:
        to_updates['full_name'] = full_name
    if email_domain:
        to_updates['email_domain'] = email_domain
    if is_disabled is not None:
        to_updates['is_disabled'] = is_disabled

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    if not to_updates:
        return

    async with OnlyExecute(
            event='update institute by id',
            sql=fr'UPDATE institute'
                fr'   SET {set_sql}'
                fr' WHERE id = %(institute_id)s',
            institute_id=institute_id,
            **to_updates,
    ):
        pass
