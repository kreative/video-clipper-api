# docuvet-api

Backend for Docuvet.

## Running

Using `pipenv` for package management. - [Pipenv](https://pipenv.pypa.io/en/latest/)

```bash title="shell"
# Create Virtual Environment
pipenv shell --python 3.12
# Install Dependencies
pipenv install
# Run the API
python src/app.py
```

Using `venv` for package management. - [venv](https://docs.python.org/3/library/venv.html)

```bash title="shell"
# Create Virtual Environment
python3 -m venv venv
# Activate Virtual Environment
source venv/bin/activate
# Install Dependencies
pip install -r requirements.txt
# Run the API
python src/app.py
```
## Upgrade Database

For syncing db schema with the `models` directory

> [!WARNING] DANGER
> This alters the database and can DELETE DATA

```bash
flask db migrate -m "added prompt to section table"
flask db upgrade
```

```txt 
one day, there will be more documentation. i promise.

- yarles
```

