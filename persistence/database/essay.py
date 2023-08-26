from typing import Sequence

from base import do

from .base import FetchAll, FetchOne, OnlyExecute, ParamDict


async def browse(include_deleted=False) -> Sequence[do.Essay]:

    async with FetchAll(
            event='browse essay',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, description, is_deleted'
                fr'  FROM essay'
                fr'{" WHERE NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Essay(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                         setter_id=setter_id, description=description, is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, title, setter_id, description, is_deleted) in records]


async def browse_by_challenge(challenge_id: int, include_deleted=False) -> Sequence[do.Essay]:
    async with FetchAll(
            event='browse essays with challenge id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, description, is_deleted'
                fr'  FROM essay'
                fr' WHERE challenge_id = %(challenge_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}'
                fr' ORDER BY id ASC',
            challenge_id=challenge_id,
            raise_not_found=False,  # Issue #134: return [] for browse
    ) as records:
        return [do.Essay(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                         setter_id=setter_id, description=description, is_deleted=is_deleted)
                for (id_, challenge_id, challenge_label, title, setter_id, description, is_deleted) in records]


async def read(essay_id: int, include_deleted=False) -> do.Essay:
    async with FetchOne(
            event='read essay by id',
            sql=fr'SELECT id, challenge_id, challenge_label, title, setter_id, description, is_deleted'
                fr'  FROM essay'
                fr' WHERE id = %(essay_id)s'
                fr'{" AND NOT is_deleted" if not include_deleted else ""}',
            essay_id=essay_id,
    ) as (id_, challenge_id, challenge_label, title, setter_id, description, is_deleted):
        return do.Essay(id=id_, challenge_id=challenge_id, challenge_label=challenge_label, title=title,
                        setter_id=setter_id, description=description, is_deleted=is_deleted)


async def add(challenge_id: int, challenge_label: str, title: str, setter_id: int, description: str) -> int:
    async with FetchOne(
            event='create essay',
            sql=r'INSERT INTO essay'
                r'            (challenge_id, challenge_label, title, setter_id, description)'
                r'     VALUES (%(challenge_id)s, %(challenge_label)s, %(title)s, %(setter_id)s, %(description)s)'
                r'  RETURNING id',
            challenge_id=challenge_id,
            challenge_label=challenge_label,
            title=title, setter_id=setter_id, description=description,
    ) as (essay_id,):
        return essay_id


async def edit(essay_id: int, setter_id: int, title: str = None,  challenge_label: str = None, description: str = None):
    to_updates: ParamDict = {'setter_id': setter_id}

    if title is not ...:
        to_updates['title'] = title
    if description is not ...:
        to_updates['description'] = description
    if challenge_label is not ...:
        to_updates['challenge_label'] = challenge_label

    if not to_updates:
        return

    set_sql = ', '.join(fr"{field_name} = %({field_name})s" for field_name in to_updates)

    async with OnlyExecute(
            event='edit essay',
            sql=fr'UPDATE essay'
                fr'   SET {set_sql}'
                fr' WHERE id = %(essay_id)s',
            **to_updates,
            essay_id=essay_id,
    ):
        pass


async def delete(essay_id: int):
    async with OnlyExecute(
            event='soft delete essay',
            sql=r'UPDATE essay'
                r'   SET is_deleted = %(is_deleted)s'
                r' WHERE id = %(essay_id)s',
            is_deleted=True,
            essay_id=essay_id,
    ):
        pass
