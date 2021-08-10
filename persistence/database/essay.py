from typing import Sequence

from base import do

from .base import SafeExecutor


async def browse(include_deleted=False) -> Sequence[do.Essay]:
    filters = []

    if not include_deleted:
        filters.append("NOT is_deleted")

    cond_sql = ' AND '.join(filters)

    async with SafeExecutor(
            event='browse essay',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, description, is_deleted'
                fr'  FROM essay'
                fr' {f" WHERE {cond_sql}" if cond_sql else ""}'
                fr' ORDER BY id ASC',
            fetch='all',
    ) as records:
        return [do.Essay(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                         setter_id=setter_id, description=description, is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, title, setter_id, description, is_deleted) in records]


async def browse_by_challenge(challenge_id: int, include_deleted=False) -> Sequence[do.Essay]:
    async with SafeExecutor(
            event='browse essays with challenge id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, description, is_deleted'
                fr'  FROM essay'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            challenge_id=challenge_id,
            fetch='all',
    ) as records:
        return [do.Essay(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                         setter_id=setter_id, description=description, is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, title, setter_id, description, is_deleted) in records]


async def read(essay_id: int, include_deleted=False) -> do.Essay:
    async with SafeExecutor(
            event='read essay by id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, description, is_deleted'
                fr'  FROM essay'
                fr' WHERE id = %(essay_id)s'
                fr' {" AND NOT is_deleted" if not include_deleted else ""}',
            essay_id=essay_id,
            fetch=1,
    ) as (id_, challenge_id, challenge_label, title, setter_id, description, is_deleted):
        return do.Essay(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                        setter_id=setter_id, description=description, is_deleted=is_deleted)


async def add(challenge_id: int, challenge_label: int, title: str, setter_id: int, description: int) -> int:
    async with SafeExecutor(
            event='create essay',
            sql=fr'INSERT INTO essay'
                fr'            (challenge_id, challenge_label, title, setter_id, description)'
                fr'     VALUES (%(challenge_id)s, %(challenge_label)s, %(title)s, %(setter_id)s, %(description)s)'
                fr'  RETURNING id',
            challenge_id=challenge_id,
            challenge_label=challenge_label,
            title=title, setter_id=setter_id, description=description,
            fetch=1,
    ) as (essay_id,):
        return essay_id


async def edit(essay_id: int, setter_id: int, title: str = None, description: str = None):
    to_updates = {}

    if title is not None:
        to_updates['title'] = title
    if description is not None:
        to_updates['description'] = description

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with SafeExecutor(
            event='edit essay',
            sql=fr'UPDATE essay'
                fr'   SET {set_sql}'
                fr' WHERE id = %(essay_id)s',
            **to_updates,
            essay_id=essay_id,
    ):
        pass


async def delete(essay_id: int):
    async with SafeExecutor(
            event='soft delete essay',
            sql=fr'UPDATE essay'
                fr'   SET is_deleted = %(is_deleted)s'
                fr' WHERE id = %(essay_id)s',
            is_deleted=True,
            essay_id=essay_id,
    ):
        pass
