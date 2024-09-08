# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

define USAGE
Development:

    clean           Remove build artifacts.

Testing:

    test            Run tests.

Building:

    build           Build the Python package.
    standalone      Build the standalone toltecmk executable.

Formatting:

    format          Check that the source code formatting follows
                    the style guide.
    format-fix      Automatically reformat the source code to follow
                    the style guide.

Linting:

    lint            Perform static analysis on the source code to find
                    erroneous constructs.
    links           Check that all links in Markdown files are alive.
endef
export USAGE

help:
	@echo "$$USAGE"

.venv-build/bin/activate: requirements.build.txt
	@echo "Setting up development virtual env in .venv"
	python -m venv .venv-build; \
	. .venv-build/bin/activate; \
	python -m pip install -r requirements.build.txt

.venv-runtime/bin/activate: requirements.txt
	@echo "Setting up development virtual env in .venv"
	python -m venv .venv-runtime; \
	. .venv-runtime/bin/activate; \
	python -m pip install -r requirements.txt

clean:
	git clean --force -dX

build: .venv-build/bin/activate
	. .venv-build/bin/activate; \
	python -m build

standalone: .venv-build/bin/activate
	. .venv-build/bin/activate; \
	python -m PyInstaller --distpath . toltecmk.spec

test: .venv-runtime/bin/activate
	. .venv-runtime/bin/activate; \
	python -m unittest; \
	tests/foobar/test.sh

format: .venv-build/bin/activate
	. .venv-build/bin/activate; \
	black --line-length 80 --check --diff toltec tests

format-fix: .venv-build/bin/activate
	. .venv-build/bin/activate; \
	black --line-length 80 toltec tests

lint: .venv-build/bin/activate
	. .venv-build/bin/activate; \
	echo "==> Typechecking files"; \
	mypy --disallow-untyped-defs toltec; \
	echo "==> Linting files"; \
	pylint toltec

links:
	find . \
	    -name "*.md" \
	    -not -exec git check-ignore {} \; \
	    -exec markdown-link-check {} \;

.PHONY: \
    help \
    build \
    standalone \
    clean \
    test \
    format \
    format-fix \
    lint \
    links
