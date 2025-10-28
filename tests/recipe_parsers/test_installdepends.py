# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

import os
import re
from os import path
import unittest
from tempfile import TemporaryDirectory
from datetime import datetime, timezone
from toltec import parse_recipe
from toltec.bash import ScriptError
from toltec.recipe import Package, Recipe, Source, RecipeError, RecipeWarning
from toltec.version import (
    Version,
    Dependency,
    DependencyKind,
    VersionComparator,
)


class TestInstallDepends(unittest.TestCase):
    def setUp(self) -> None:
        self.dir_handle = TemporaryDirectory()
        self.dir = self.dir_handle.name

    def tearDown(self) -> None:
        self.dir = None
        self.dir_handle.cleanup()

    def test_installdepends(self) -> None:
        """Check that basic fields are parsed."""
        rec_path = path.join(self.dir, "toltec-base")
        os.makedirs(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
archs=(rmall rmallos2 rmallos3 rm1 rm1os2 rm1os3 rm2 rm2os2 rm2os3 rmpp rmppos3)
pkgnames=(toltec-base)
pkgdesc="Metapackage defining the base set of packages in a Toltec install"
url=https://toltec-dev.org/
pkgver=1.4-1
timestamp=2023-12-27T08:30Z
section="utils"
maintainer="Eeems <eeems@eeems.email>"
license=MIT
installdepends=(toltec-bootstrap toltec-deletions toltec-completion launcherctl wget-ssl ca-certificates entware-rc)
installdepends_rm1os2=(open-remarkable-shutdown)
installdepends_rm1os3=(open-remarkable-shutdown)
installdepends_rm2os2=(rm2-suspend-fix)
installdepends_rm2os3=(rm2-suspend-fix)
installdepends_rmpp=(rmpp-make-root-rw)
installdepends_rmppos3=(rmpp-make-root-rw)
installdepends_rmppm=(rmpp-make-root-rw)
installdepends_rmppmos3=(rmpp-make-root-rw)

image=base:v2.1
source=("https://example.org/toltec/${pkgnames[0]}/release-${pkgver%-*}.zip")
sha256sums=(SKIP)

build() {
    echo "Build function"
}

package() {
    echo "Package function"
}
"""
            )

        basic_depends = [
            Dependency(DependencyKind.HOST, x)
            for x in [
                "toltec-bootstrap",
                "toltec-deletions",
                "toltec-completion",
                "launcherctl",
                "wget-ssl",
                "ca-certificates",
                "entware-rc",
            ]
        ]
        rm1_depends = [
            Dependency(DependencyKind.HOST, "open-remarkable-shutdown")
        ]
        rm2_depends = [Dependency(DependencyKind.HOST, "rm2-suspend-fix")]
        rmpp_depends = [Dependency(DependencyKind.HOST, "rmpp-make-root-rw")]
        rmppm_depends = [Dependency(DependencyKind.HOST, "rmpp-make-root-rw")]

        recipes = parse_recipe(rec_path)

        self.assertEqual(
            list(recipes.keys()),
            [
                "rmall",
                "rmallos2",
                "rmallos3",
                "rm1",
                "rm1os2",
                "rm1os3",
                "rm2",
                "rm2os2",
                "rm2os3",
                "rmpp",
                "rmppos3",
                "rmppm",
                "rmppmos3",
            ],
        )
        recipe = recipes["rmall"]
        self.assertIs(type(recipe), Recipe)
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        package = recipe.packages["toltec-base"]
        self.assertEqual(
            package.installdepends,
            set(basic_depends),
        )

        recipe = recipes["rm1"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends),
        )

        recipe = recipes["rm2"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends),
        )

        recipe = recipes["rmallos2"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends),
        )

        recipe = recipes["rmallos3"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends),
        )

        recipe = recipes["rm1os2"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rm1_depends),
        )

        recipe = recipes["rm1os3"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rm1_depends),
        )

        recipe = recipes["rm2os2"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rm2_depends),
        )

        recipe = recipes["rm2os3"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rm2_depends),
        )

        recipe = recipes["rmpp"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rmpp_depends),
        )

        recipe = recipes["rmppos3"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rmpp_depends),
        )

        recipe = recipes["rmppm"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rmppm_depends),
        )

        recipe = recipes["rmppmos3"]
        self.assertIs(type(recipe), Recipe)
        package = recipe.packages["toltec-base"]
        self.assertEqual(list(recipe.packages.keys()), ["toltec-base"])
        self.assertEqual(
            package.installdepends,
            set(basic_depends + rmppm_depends),
        )
