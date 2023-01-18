#!/usr/bin/env python3
# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""Build packages from the recipe in [DIR]."""

import argparse
import logging
import os
import sys
from typing import Dict, List, Optional
from toltec import parse_recipe
from toltec.builder import Builder
from toltec.recipe import Package
from toltec.repo import make_index
from toltec.util import argparse_add_verbose, LOGGING_FORMAT

def make_argparser():
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
        "-s",
        "--source-dir",
        metavar="DIR",
        default=None,
        help="""path to the source directory
        (optional: when specified, a local build is performed instead of fetching 
                   sources)""",
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
        help="""list of packages to build (default: all packages from the recipe,
        can be repeated)""",
    )

    argparse_add_verbose(parser)
    return parser

if __name__ == '__main__':
    args = make_argparser().parse_args()
    logging.basicConfig(format=LOGGING_FORMAT, level=args.verbose)

    recipe_bundle = parse_recipe(args.recipe_dir)
    builder = Builder(args.work_dir, args.dist_dir, args.source_dir)

    build_matrix: Optional[Dict[str, Optional[List[Package]]]] = None

    if args.arch_name or args.package_name:
        build_matrix = {}

        for arch, recipes in recipe_bundle.items():
            if args.package_name:
                build_matrix[arch] = [
                    recipes.packages[pkg_name] for pkg_name in args.package_name
                ]
            else:
                build_matrix[arch] = None

    if not builder.make(recipe_bundle, build_matrix):
        sys.exit(1)

    make_index(args.dist_dir)
