
.PHONY: all
all: dependencies

.venv:
	python -m venv .venv

.PHONY: dependencies
dependencies: .venv
	source .venv/bin/activate && pip install -e .[dev]
	source .venv/bin/activate && pip install -e ../../.
