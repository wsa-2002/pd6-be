from typing import Sequence

import log
from base import do

from .base import SafeExecutor


async def add(name: str, email_domain: str, is_disabled: bool) -> int:
    async with SafeExecutor(
            event='Add institute',
            sql=r'INSERT INTO institute'
                r'            (name, email_domain, is_disabled)'
                r'     VALUES (%(name)s, %(email_domain)s, %(is_disabled)s)'
                r'  RETURNING id',
            name=name,
            email_domain=email_domain,
            is_disabled=is_disabled,
            fetch=1,
    ) as (institute_id,):
        return institute_id


async def browse(*, include_disabled=False) -> Sequence[do.Institute]:
    async with SafeExecutor(
            event='get all institutes',
            sql=fr'SELECT id, name, email_domain, is_disabled'
                fr'  FROM institute'
                fr'{" WHERE NOT is_disabled" if not include_disabled else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.Institute(id=id_, name=name, email_domain=email_domain, is_disabled=is_disabled)
                for (id_, name, email_domain, is_disabled) in records]


async def read(institute_id: int, *, include_disabled=True) -> do.Institute:
    async with SafeExecutor(
            event='get all institutes',
            sql=fr'SELECT id, name, email_domain, is_disabled'
                fr'  FROM institute'
                fr' WHERE id = %(institute_id)s'
                fr'{" WHERE NOT is_disabled" if not include_disabled else ""}'
                fr' ORDER BY id',
            institute_id=institute_id,
            fetch=1,
    ) as (id_, name, email_domain, is_disabled):
        return do.Institute(id=id_, name=name, email_domain=email_domain, is_disabled=is_disabled)


async def edit(institute_id: int, name: str = None, email_domain: str = None, is_disabled: bool = None) -> None:
    to_updates = {}

    if name:
        to_updates['name'] = name
    if email_domain:
        to_updates['email_domain'] = email_domain
    if is_disabled is not None:
        to_updates['is_disabled'] = is_disabled

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    if not to_updates:
        return

    async with SafeExecutor(
            event='update institute by id',
            sql=fr'UPDATE institute'
                fr'   SET {set_sql}'
                fr' WHERE id = %(institute_id)s',
            institute_id=institute_id,
            **to_updates,
    ):
        pass
