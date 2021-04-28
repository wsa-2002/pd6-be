from typing import Sequence, Collection

from base.enum import CourseType, RoleType

from . import do
from .base import SafeExecutor, SafeConnection


async def create(name: str, course_id: int, is_enabled: bool, is_hidden: bool) -> int:
    async with SafeExecutor(
            event='create class',
            sql=r'INSERT INTO class'
                r'            (name, course_id, is_enabled, is_hidden)'
                r'     VALUES (%(name)s, %(course_id)s), %(is_enabled)s), %(is_hidden)s)'
                r'  RETURNING id',
            name=name,
            course_id=course_id,
            is_enabled=is_enabled,
            is_hidden=is_hidden,
            fetch=1,
    ) as (course_id,):
        return course_id
