from typing import Sequence

from base import do

from .base import SafeExecutor


async def add(name: str, email_domain: str) -> int:
    async with SafeExecutor(
            event='Add institute',
            sql=r'INSERT INTO institute'
                r'            (name, email_domain)'
                r'     VALUES (%(name)s, %(email_domain)s)'
                r'  RETURNING id',
            name=name,
            email_domain=email_domain,
            fetch=1,
    ) as (institute_id,):
        return institute_id


async def browse(only_enabled=True) -> Sequence[do.Institute]:
    async with SafeExecutor(
            event='get all institutes',
            sql=fr'SELECT id, name, email_domain, is_enabled'
                fr'  FROM institute'
                fr'{" WHERE is_enabled = TRUE" if only_enabled else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.Institute(id=id_, name=name, email_domain=email_domain, is_enabled=is_enabled)
                for (id_, name, email_domain, is_enabled) in records]


async def read(institute_id: int, only_enabled=True) -> do.Institute:
    async with SafeExecutor(
            event='get all institutes',
            sql=fr'SELECT id, name, email_domain, is_enabled'
                fr'  FROM institute'
                fr' WHERE id = %(institute_id)s'
                fr' {"AND is_enabled = TRUE" if only_enabled else ""}'
                fr' ORDER BY id',
            institute_id=institute_id,
            fetch=1,
    ) as (id_, name, email_domain, is_enabled):
        return do.Institute(id=id_, name=name, email_domain=email_domain, is_enabled=is_enabled)


async def edit(institute_id: int, name: str = None, email_domain: str = None, is_enabled: bool = None) -> None:
    to_updates = {}

    if name:
        to_updates['name'] = name
    if email_domain:
        to_updates['email_domain'] = email_domain
    if is_enabled is not None:
        to_updates['is_enabled'] = is_enabled

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    if not to_updates:
        return

    async with SafeExecutor(
            event='update institute by id',
            sql=fr'UPDATE institute'
                fr' WHERE institute.id = %(institute_id)s'
                fr'   SET {set_sql}',
            institute_id=institute_id,
            **to_updates,
    ):
        pass
