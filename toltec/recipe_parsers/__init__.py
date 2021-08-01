# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""Recipe parsers."""

from . import bash
from ..recipe import RecipeBundle


parsers = (bash,)


def parse(path: str) -> RecipeBundle:
    """
    Load a recipe defined using any of the supported formats.

    :param path: path to the directory containing the recipe definition
    :raises RecipeError: if there is an error in the recipe
    :raises FileNotFoundError: if no recipe is found at the given path
    :returns: loaded recipe
    """
    for parser in parsers:
        try:
            # See <https://github.com/python/mypy/issues/9841>
            # and <https://github.com/python/mypy/issues/5018>
            return parser.parse(path)  # type: ignore
        except FileNotFoundError:
            pass

    raise FileNotFoundError(
        f"No recipe in a compatible format found in '{path}'"
    )
