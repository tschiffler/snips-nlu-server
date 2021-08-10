# Setup
## Python
https://realpython.com/installing-python/

### Create virtual environment
```sh
$ python -m venv venv/
```

Additionally you need to activate the environment.
```sh
$ source venv/bin/activate
```
Depending on your shell you might need to run another script, read more [here](https://docs.python.org/3/tutorial/venv.html)

Install dependencies:
```sh
$ pip install -r requirements.txt
```

## Snips NLU
```sh
$ python -m snips-nlu download <language>
# or natively
$ snips-nlu download <language>
```

## Flask
```sh
# Linux/MacOS
$ export FLASK_APP=server/__init__.py
# Windows
$ set FLASK_APP=server/__init__.py
```

If you want to restart the server on changes automatically, add this to your environment:
```sh
# Linux/MacOS
$ export FLASK_ENV=development
# Windows
$ set FLASK_ENV=development
```
# Run your server
```sh
$ python -m flask run
# or natively
$ flask run
```