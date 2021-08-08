# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

define USAGE
Testing:

    test            Run tests.

Building:

    build           Build the Python package.
    clean           Remove build artifacts.

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

build:
	python -m build

clean:
	rm -rf toltec.egg-info dist

test:
	python -m unittest

format:
	black --line-length 80 --check --diff toltec tests

format-fix:
	black --line-length 80 toltec tests

lint:
	@echo "==> Typechecking files"
	mypy --disallow-untyped-defs toltec
	@echo "==> Linting files"
	pylint toltec

links:
	find . \
	    -name "*.md" \
	    -not -exec git check-ignore {} \; \
	    -exec markdown-link-check {} \;

.PHONY: \
    help \
    build \
    clean \
    test \
    format \
    format-fix \
    lint \
    links
