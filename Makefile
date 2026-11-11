PYTHON ?= python3

run:
	@$(PYTHON) -m examshell

check:
	@$(PYTHON) -m examshell --check

check-piscine:
	@$(PYTHON) -m examshell --check piscine

check-python check-current:
	@$(PYTHON) -m examshell --check python

check-c check-old:
	@$(PYTHON) -m examshell --check c

selftest:
	@$(PYTHON) scripts/selftest.py

clean:
	@rm -rf rendu trace
	@find . -name __pycache__ -prune -exec rm -rf {} +

.PHONY: run check check-piscine check-python check-c check-current check-old selftest clean
