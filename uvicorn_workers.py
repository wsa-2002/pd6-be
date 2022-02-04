import uvicorn.workers


class UvicornWorker(uvicorn.workers.UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "auto",
        "http": "auto",
        "proxy_headers": True,
        'forwarded_allow_ips': '*',
    }
