import typing

import fastapi.routing


class JSONResponse(fastapi.routing.JSONResponse):
    def __init__(self, *args, success=True, error: Exception = None, **kwargs):
        self._success = success
        self._error = error
        super().__init__(*args, **kwargs)

    def render(self, content: typing.Any) -> bytes:
        return super().render({
            'success': self._success,
            'data': content,
            'error': str(self._error) if self._error else None,
        })


async def exception_handler(request, error: Exception):
    return JSONResponse(success=False, error=error)
