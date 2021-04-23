# PDOGS 6: Async

A `python=3.8`-`asyncio`-based version, using web framework `fastapi`.

*Please* do proper research about `python`'s `asyncio` before committing to this project.

## Setup test server

### 0. `python`
Using `conda` as example:
```shell
conda create --name pdogs6-async --python=3.8
conda activate pdogs6-async
```

### 1. Environment
```shell
pip install -r requirements.txt
cp .env.example .env
```

Then fill out the environment variables in `.env`.

### 2. Start the server
```shell
pip install uvicorn
uvicorn app:app --reload
```

On your terminal you should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process xxxx using watchgod
INFO:     Started server process xxxx
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

You may also change the host & port with `--host` and `--port`:
```shell
uvicorn app:app --reload --host 0.0.0.0 --port 80
```
