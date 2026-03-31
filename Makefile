PYTHON ?= python
PIP ?= pip

.PHONY: setup lint test format airflow-init airflow-start

setup:
	$(PIP) install -r requirements/base.txt -r requirements/dev.txt
	pre-commit install

lint:
	ruff check .
	mypy src

test:
	pytest -q

format:
	ruff check . --fix
	ruff format .

airflow-init:
	AIRFLOW_HOME=.airflow airflow db migrate
	AIRFLOW_HOME=.airflow airflow users create --username admin --firstname RevOps --lastname Admin --role Admin --email admin@example.com --password admin

airflow-start:
	AIRFLOW_HOME=.airflow airflow standalone
