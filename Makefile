# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

define USAGE
Available commands:

    test            Run unit tests.
    format          Check that the source code formatting follows
                    the style guide.
    format-fix      Automatically reformat the source code to follow
                    the style guide.
    lint            Perform static analysis on the source code to find
                    erroneous constructs.
endef
export USAGE

help:
	@echo "$$USAGE"

test:
	python -m unittest

format:
	black --line-length 80 --check --diff toltec tests toltecmk

format-fix:
	black --line-length 80 toltec tests toltecmk

lint:
	@echo "==> Typechecking files"
	mypy --disallow-untyped-defs toltec toltecmk
	@echo "==> Linting files"
	pylint toltec toltecmk

.PHONY: \
    help \
    test \
    format \
    format-fix \
    lint
