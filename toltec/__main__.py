# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""Build packages from the recipe in [DIR]."""

import argparse
import os
import sys
from importlib.util import find_spec, spec_from_file_location, module_from_spec
from typing import Dict, List, Optional
from toltec import parse_recipe
from toltec.builder import Builder
from toltec.recipe import Package
from toltec.repo import make_index
from toltec import util


def main() -> int:  # pylint:disable=too-many-branches
    """Execute requested commands and return appropriate exit code."""
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "recipe_dir",
        metavar="DIR",
        nargs="?",
        default=os.getcwd(),
        help="""path to a directory containing the recipe to build
        (default: current directory)""",
    )

    parser.add_argument(
        "-w",
        "--work-dir",
        metavar="DIR",
        default=os.path.join(os.getcwd(), "build"),
        help="""path to a directory used for building the package
        (default: [current directory]/build)""",
    )

    parser.add_argument(
        "-d",
        "--dist-dir",
        metavar="DIR",
        default=os.path.join(os.getcwd(), "dist"),
        help="""path to a directory where built packages are stored
        (default: [current directory]/dist)""",
    )

    parser.add_argument(
        "-a",
        "--arch-name",
        metavar="ARCHNAME",
        action="append",
        help="""only build for the given architecture (can
        be repeated)""",
    )

    parser.add_argument(
        "-p",
        "--package-name",
        metavar="PACKAGENAME",
        action="append",
        help="""list of packages to build (default: all packages from the
        recipe, can be repeated)""",
    )

    parser.add_argument(
        "-H",
        "--hook",
        metavar="PATH",
        action="append",
        help="""name or path to a Python module that registers listeners for
        build hooks (can be repeated) - if a path is passed, it must start with
        either a dot or a slash""",
    )

    util.argparse_add_verbose(parser)
    util.argparse_add_warning(parser)
    args = parser.parse_args()
    util.setup_logging(args)

    recipe_bundle = parse_recipe(args.recipe_dir)

    with Builder(args.work_dir, args.dist_dir) as builder:
        if args.hook:
            for ident in args.hook:
                if ident and ident[0] in (".", "/"):
                    spec = spec_from_file_location("toltec.hooks.user", ident)
                else:
                    spec = find_spec(ident)

                if spec:
                    module = module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore
                    module.register(builder)  # type: ignore
                else:
                    raise RuntimeError(
                        f"Hook module '{ident}' couldn’t be loaded"
                    )

        build_matrix: Optional[Dict[str, Optional[List[Package]]]] = None

        if args.arch_name or args.package_name:
            build_matrix = {}

            for arch, recipes in recipe_bundle.items():
                if args.package_name:
                    build_matrix[arch] = [
                        recipes.packages[pkg_name]
                        for pkg_name in args.package_name
                    ]
                else:
                    build_matrix[arch] = None

        if not builder.make(recipe_bundle, build_matrix):
            return 1

    make_index(args.dist_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
