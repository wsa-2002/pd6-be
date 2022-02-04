import asyncio
from typing import Sequence

import aiohttp


async def _download(session: aiohttp.ClientSession, url: str) -> bytes:
    async with session.get(url) as resp:
        return await resp.read()


async def download(url: str) -> bytes:
    async with aiohttp.ClientSession() as session:
        return await _download(session, url)


async def batch_download(*urls: str) -> Sequence[bytes]:
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[_download(session, url) for url in urls])
