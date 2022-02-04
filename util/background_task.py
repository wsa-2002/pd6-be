from typing import Callable, Coroutine

from fastapi import BackgroundTasks

import log


def launch(background_task: BackgroundTasks, task: Callable[..., Coroutine], *args, **kwargs):
    async def _wrapped_task():
        try:
            await task(*args, **kwargs)
        except Exception as e:
            log.exception(e)

    background_task.add_task(_wrapped_task)
