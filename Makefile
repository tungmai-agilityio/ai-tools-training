.PHONY: install build test lint

install:
	python -m pip install -r requirements-dev.txt

build:
	python -m pip install -r requirements.txt

test:
	pytest -q

# ponytail: byte-compile syntax check only; no linter is a project dependency (adding ruff needs approval).
lint:
	python -m compileall -q app tests scripts
