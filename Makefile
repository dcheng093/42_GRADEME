PYTHON ?= python3
# the flags 42's Python subjects ask for
MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	--disallow-untyped-defs --check-untyped-defs \
	--no-error-summary --cache-dir=$(CURDIR)/.mypy_cache

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

# every subject folder has its own solution.py / tests.py: checked one by one
lint:
	@flake8 $$(git ls-files '*.py')
	@mypy $(MYPY_FLAGS) -p examshell
	@for f in scripts/*.py; do mypy $(MYPY_FLAGS) $$f || exit 1; done
	@for d in $$(git ls-files 'subjects/*.py' | xargs -n1 dirname | sort -u); do \
		(cd $$d && MYPYPATH=$(CURDIR) mypy $(MYPY_FLAGS) *.py) || exit 1; \
	done
	@echo "flake8 + mypy: clean"

clean:
	@rm -rf rendu trace .mypy_cache
	@find . -name __pycache__ -prune -exec rm -rf {} +

.PHONY: run check check-piscine check-python check-c check-current check-old selftest lint clean
