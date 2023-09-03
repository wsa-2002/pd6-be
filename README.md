# `pd6-be`: Async Web Backend for PDOGS 6

A `python=3.10`-`asyncio`-based web backend, using web framework `fastapi`.

*Please* do proper research about `python`'s `asyncio` before committing to this project.

## Setup test server

### 1. `git`
Add `--recursive` in your command in order to clone both `pd6-be` and its submodule `common`(`pd6-common`). 
```shell
git clone --recursive ssh://git@git.ntu.im:30001/pdogs/pdogs-6/pd6-be.git
```

### 2. `python`

> Suggest using PyCharm for development tool; you may also connect your `conda` environment with PyCharm!

Using `conda` as example:
```shell
conda create --name pd6-be python=3.10
conda activate pd6-be
```

### 3. Environment
```shell
pip install -r requirements.txt
cp .env.example .env
cp logging.yaml.example logging.yaml
```

Then
1. Fill out the environment variables in `.env`.
2. Check the `filename`s in `logging.yaml`, and replace if you needed.
3. Check the `propagate`s in `logging.yaml`, and replace with `True` if you want to show that genre of log on your console.
4. Manually create your log folder (default `/log` under your cloned `pd6-be` project folder).

### 4. Start the server

```shell
pip install uvicorn
uvicorn main:app
```

On your terminal you should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process xxxx using watchgod
INFO:     Started server process xxxx
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
Now you can go to `http://127.0.0.1:8000` and test it.  
You may also turn up the auto-reload option, or change the host & port with `--host` and `--port`:
```shell
uvicorn main:app --reload --host 0.0.0.0 --port 80
```

## Unit tests

### Run test
```shell
python -m run_test
```
or
```shell
python run_test.py
```

### Coverage

```shell
coverage run -m run_test -v
# coverage report
coverage report
```

## Linter

```shell
pip install ruff
ruff .
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
- [Color of Bikeshed](https://bikeshed.com/)
- [If it ain't broke, don't fix it](https://en.wikipedia.org/wiki/Bert_Lance#If_it_ain't_broke,_don't_fix_it)
- [Zen of Python](https://www.python.org/dev/peps/pep-0020/)
- [Premature optimization is the root of all evil](https://en.wikiquote.org/wiki/Donald_Knuth#Computer_Programming_as_an_Art_(1974));
  [some discussion](https://softwareengineering.stackexchange.com/questions/80084/is-premature-optimization-really-the-root-of-all-evil)
- [SRP: Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)

### BREAD
This project adapts the BREAD concept: Browse, Read, Edit, Add, Delete.
It is similar to CRUD (Create, Read, Update, Delete), but with an additional "Browse".  

For Browse in this project, it is batch reading with pagination.

#### Why not CRUD (or DAVE, or whatever)
Because -- the creator of this project likes BREAD.

If you feel uncomfortable about this, you should go back to the main principles and read [Color of Bikeshed](https://bikeshed.com/).

### IDE (PyCharm) Settings

The recommended (actually *forced*) IDE for this project is PyCharm >= 2021.3.
This is to
1. ensure the code style for everyone; 
2. ensure that you get the correct type hinting.
Please try not use VSCode or other IDEs to code in this project.

PyCharm Professional is free for educational users. You may register a pro account for yourself with your `@ntu.edu.tw`
email. Since the Professional version provides additional useful functionalities such as in-line SQL check, please
apply your pro account and use the Professional version.

Here are some recommended settings to apply to your PyCharm Professional, so your IDE will not raise too many 
false alarms:

#### `.dic`

Config location: Editor > Natural Languages > Spelling

You can add `.dic` file to the "Custom dictionaries" list, so PyCharm will not raise unwanted typos. You may also update
the `.dic` list as you want.

#### Inspections

Here are some inspection (Editor > Inspections) configurations that are recommended. You can avoid having to manually 
scan through the long list by entering the inspection item to the search bar.

| Type |       Inspection Item        | Severity |
|:----:| ---------------------------- |:--------:|
| SQL  | Redundant ordering direction |   Typo   |

Also, you can set `Profile` in (Editor > Inspection) to `Project Default` to ignore some inspections in test files 
and highlight test files in sidebar.
