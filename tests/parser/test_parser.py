# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

from os import path
import unittest
from datetime import datetime, timezone
from toltec import parse_recipe
from toltec.recipe import Package, Recipe, Source, Version


class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = path.dirname(path.realpath(__file__))

    def test_basic_recipe(self) -> None:
        rec_path = path.join(self.dir, "001-basic-recipe")
        recipes = parse_recipe(rec_path)

        self.assertEqual(list(recipes.keys()), ["rmall"])
        self.assertIs(type(recipes["rmall"]), Recipe)

        recipe = recipes["rmall"]

        self.assertEqual(recipe.path, rec_path)
        self.assertEqual(
            recipe.timestamp, datetime(2021, 7, 31, 20, 44, 0, 0, timezone.utc)
        )
        self.assertEqual(
            recipe.sources,
            {
                Source(
                    url="https://example.org/toltec/basic-recipe/release-42.0.zip",
                    checksum="SKIP",
                    noextract=False,
                ),
            },
        )
        self.assertEqual(recipe.makedepends, set())
        self.assertEqual(recipe.maintainer, "None <none@example.org>")
        self.assertEqual(recipe.image, "base:v2.1")
        self.assertEqual(recipe.arch, "rmall")
        self.assertEqual(recipe.flags, [])
        self.assertEqual(recipe.prepare, "")
        self.assertEqual(
            recipe.build,
            """\
declare -a flags=()
declare -- timestamp=2021-07-31T20:44Z
declare -a source=([0]=https://example.org/toltec/basic-recipe/release-42.0.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -- maintainer='None <none@example.org>'
declare -- image=base:v2.1
declare -- arch=rmall
declare -- license=MIT
declare -- pkgdesc='A simple test for recipe parsing'
declare -- pkgver=42.0-1
declare -- section=test
declare -- url=https://example.org/toltec/basic-recipe

package() {

    echo "Package function"

}

    echo "Build function"
""",
        )

        self.assertEqual(list(recipe.packages.keys()), ["basic-recipe"])
        self.assertIs(type(recipe.packages["basic-recipe"]), Package)

        package = recipe.packages["basic-recipe"]

        self.assertEqual(package.name, "basic-recipe")
        self.assertEqual(package.parent, recipe)
        self.assertEqual(package.version, Version(0, "42.0", "1"))
        self.assertEqual(package.desc, "A simple test for recipe parsing")
        self.assertEqual(package.url, "https://example.org/toltec/basic-recipe")
        self.assertEqual(package.section, "test")
        self.assertEqual(package.license, "MIT")
        self.assertEqual(package.installdepends, set())
        self.assertEqual(package.conflicts, set())
        self.assertEqual(package.replaces, set())
        self.assertEqual(
            package.package,
            """\
declare -a flags=()
declare -- timestamp=2021-07-31T20:44Z
declare -a source=([0]=https://example.org/toltec/basic-recipe/release-42.0.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -- maintainer='None <none@example.org>'
declare -- image=base:v2.1
declare -- arch=rmall
declare -- pkgname=basic-recipe
declare -- pkgver=42.0-1
declare -- pkgdesc='A simple test for recipe parsing'
declare -- url=https://example.org/toltec/basic-recipe
declare -- section=test
declare -- license=MIT
declare -a installdepends=()
declare -a conflicts=()
declare -a replaces=()


    echo "Package function"
""",
        )
        self.assertEqual(package.preinstall, "")
        self.assertEqual(package.configure, "")
        self.assertEqual(package.preupgrade, "")
        self.assertEqual(package.postupgrade, "")
        self.assertEqual(package.preremove, "")
        self.assertEqual(package.postremove, "")
        self.assertEqual(package.pkgid(), "basic-recipe_42.0-1_rmall")
        self.assertEqual(
            package.filename(), "rmall/basic-recipe_42.0-1_rmall.ipk"
        )
        self.assertEqual(
            package.control_fields(),
            """\
Package: basic-recipe
Description: A simple test for recipe parsing
Homepage: https://example.org/toltec/basic-recipe
Version: 42.0-1
Section: test
Maintainer: None <none@example.org>
License: MIT
Architecture: rmall
""",
        )
