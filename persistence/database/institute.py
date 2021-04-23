from typing import Optional

from . import do
from .base import SafeExecutor


async def add_institute() -> int:
    async with SafeExecutor(
        event='',
        commit=True,
    ) as (institute_id,):
        return institute_id
