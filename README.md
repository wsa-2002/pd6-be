# PDOGS 6: Async

A `python=3.8`-`asyncio`-based version, using web framework `fastapi`.

*Please* do proper research about `python`'s `asyncio` before committing to this project.

## Setup test server

### 0. `python`
> Suggest using PyCharm for development tool; you may also connect your `conda` environment with PyCharm!

Using `conda` as example:
```shell
conda create --name pdogs6-async python=3.9
conda activate pdogs6-async
```

### 1. Environment
```shell
pip install -r requirements.txt
cp .env.example .env
cp logging.yaml.example logging.yaml
```

Then
1. Fill out the environment variables in `.env`.
2. Check the `filename`s in `logging.yaml`, and replace if you needed.
3. Check the `propagate`s in `logging.yaml`, and replace with `True` if you want to show that genre of log on your console.
4. Manually create your log folder (default `/log` under your cloned `PD6-BE` project folder).

### 2. Start the server

```shell
pip install uvicorn
uvicorn main:app --reload
```

On your terminal you should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process xxxx using watchgod
INFO:     Started server process xxxx
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
Now you can go to http://127.0.0.1:8000 and test it.  
You may also change the host & port with `--host` and `--port`:
```shell
uvicorn main:app --reload --host 0.0.0.0 --port 80
```

## About this project

### Main Principles

> These are the _very_, **very**, **_VERY_** important principles that all developers of this project should take concern of.
> You should definitely read all of these and take them in your mind.
> 
> These principles are so important that you will benefit from those for a very, very long time,
> until you quit being a developer.
> 
> Be a good dev!

- [DRY: Don't Repeat Yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [KISS: Keep It Simple & Stupid](https://en.wikipedia.org/wiki/KISS_principle)
- [YAGNI: You Ain't Gonna Need It](https://en.wikipedia.org/wiki/You_aren%27t_gonna_need_it)
- [Color of Bikeshed](https://yellow.bikeshed.com/)
- [If it ain't broke, don't fix it](https://en.wikipedia.org/wiki/Bert_Lance#If_it_ain't_broke,_don't_fix_it)
- [Zen of Python](https://www.python.org/dev/peps/pep-0020/)

### BREAD
This project adapts the BREAD concept: Browse, Read, Edit, Add, Delete.
It is similar to CRUD (Create, Read, Update, Delete), but with an additional "Browse".  

For Browse in this project, it is batch reading with pagination.

#### Why not CRUD (or DAVE, or whatever)
Because -- the creator of this project likes BREAD.

If you feel uncomfortable about this, you should go back to the main principles and read [Color of Bikeshed](https://yellow.bikeshed.com/).
