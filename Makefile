PYTHON ?= python3

run:
	@$(PYTHON) -m examshell

check:
	@$(PYTHON) -m examshell --check

check-current:
	@$(PYTHON) -m examshell --check current

check-old:
	@$(PYTHON) -m examshell --check old

selftest:
	@$(PYTHON) scripts/selftest.py

clean:
	@rm -rf rendu trace
	@find . -name __pycache__ -prune -exec rm -rf {} +

.PHONY: run check check-current check-old selftest clean
