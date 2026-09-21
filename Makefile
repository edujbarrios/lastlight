PYTHON ?= python3
PACK ?=

.PHONY: test eval

test:
	$(PYTHON) -m unittest discover -s tests

eval:
	@test -n "$(PACK)" || (echo "Usage: make eval PACK=path/to/pack.zip"; exit 2)
	$(PYTHON) src/main.py --knowledge "$(PACK)" --eval
