PYTHON ?= python3

.PHONY: run test eval

run:
	$(PYTHON) src/main.py

test:
	$(PYTHON) -m unittest discover -s tests

eval:
	$(PYTHON) src/main.py --eval

