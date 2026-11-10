PYTHON ?= python3

run:
	@$(PYTHON) -m examshell

check:
	@$(PYTHON) -m examshell --check

clean:
	@rm -rf rendu trace
	@find . -name __pycache__ -prune -exec rm -rf {} +

.PHONY: run check clean
