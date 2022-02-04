import os

from pyinstrument import Profiler

from config import profiler_config
from middleware.envelope import middleware_error_enveloped
from util.context import context


@middleware_error_enveloped
async def middleware(request, call_next):
    if not profiler_config.enabled or request.scope['type'] != 'http':
        return await call_next(request)

    profiler = Profiler(interval=profiler_config.interval)
    profiler.start()

    try:
        return await call_next(request)
    finally:
        profiler.stop()
        with open(os.path.join(profiler_config.file_dir, str(context.get_request_uuid())), 'w+') as outfile:
            outfile.write(profiler.output_text(show_all=True, timeline=True))
