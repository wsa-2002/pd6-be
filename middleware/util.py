import fastapi


# Following fix is for getting request body in middlewares
# https://github.com/tiangolo/fastapi/issues/394#issuecomment-796652001


async def _set_body(request: fastapi.Request, body: bytes):
    async def receive():
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_request_body(request: fastapi.Request):
    request_body = await request.body()
    await _set_body(request, request_body)
    return request_body
