# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

from os import path
import unittest
from datetime import datetime, timezone
from toltec import parse_recipe
from toltec.recipe import Package, Recipe, Source
from toltec.version import Version, Dependency, DependencyKind


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
declare -- pkgname=basic-recipe


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

    def test_split_packages(self):
        rec_path = path.join(self.dir, "002-split-packages")
        recipe = parse_recipe(rec_path)["rmall"]

        self.assertEqual(recipe.path, rec_path)
        self.assertEqual(recipe.makedepends, set())
        self.assertEqual(recipe.maintainer, "None <none@example.org>")
        self.assertEqual(recipe.image, "base:v2.1")
        self.assertEqual(recipe.arch, "rmall")
        self.assertEqual(recipe.flags, [])
        self.assertEqual(
            recipe.prepare,
            """\
declare -a flags=()
declare -- timestamp=2021-08-01T10:27Z
declare -a source=([0]=https://example.org/toltec/pkg/release-4.3.2.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -- maintainer='None <none@example.org>'
declare -- image=base:v2.1
declare -- arch=rmall
declare -- _upver=4.3.2
declare -a installdepends=([0]=dep)
declare -- license=MIT
declare -- pkgver=5:4.3.2-1


    echo "Prepare function"
""",
        )
        self.assertEqual(
            recipe.build,
            """\
declare -a flags=()
declare -- timestamp=2021-08-01T10:27Z
declare -a source=([0]=https://example.org/toltec/pkg/release-4.3.2.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -- maintainer='None <none@example.org>'
declare -- image=base:v2.1
declare -- arch=rmall
declare -- _upver=4.3.2
declare -a installdepends=([0]=dep)
declare -- license=MIT
declare -- pkgver=5:4.3.2-1


    echo "Build function"
""",
        )

        pkg1 = recipe.packages["pkg1"]

        self.assertEqual(pkg1.name, "pkg1")
        self.assertEqual(pkg1.parent, recipe)
        self.assertEqual(pkg1.version, Version(5, "4.3.2", "1"))
        self.assertEqual(pkg1.desc, "First package")
        self.assertEqual(pkg1.url, "https://example.org/toltec/pkg/pkg1")
        self.assertEqual(pkg1.section, "first")
        self.assertEqual(pkg1.license, "MIT")
        self.assertEqual(
            pkg1.installdepends,
            {
                Dependency(DependencyKind.HOST, "dep"),
            },
        )
        self.assertEqual(pkg1.conflicts, set())
        self.assertEqual(pkg1.replaces, set())
        self.assertEqual(
            pkg1.package,
            """\
declare -a flags=()
declare -- timestamp=2021-08-01T10:27Z
declare -a source=([0]=https://example.org/toltec/pkg/release-4.3.2.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -- maintainer='None <none@example.org>'
declare -- image=base:v2.1
declare -- arch=rmall
declare -- pkgname=pkg1
declare -- pkgver=5:4.3.2-1
declare -- pkgdesc='First package'
declare -- url=https://example.org/toltec/pkg/pkg1
declare -- section=first
declare -- license=MIT
declare -a installdepends=([0]=dep)
declare -a conflicts=()
declare -a replaces=()
declare -- _upver=4.3.2


    echo "First package function"
""",
        )

        pkg2 = recipe.packages["pkg2"]

        self.assertEqual(pkg2.name, "pkg2")
        self.assertEqual(pkg2.parent, recipe)
        self.assertEqual(pkg2.version, Version(5, "4.3.2", "1"))
        self.assertEqual(pkg2.desc, "Second package")
        self.assertEqual(pkg2.url, "https://example.org/toltec/pkg/pkg2")
        self.assertEqual(pkg2.section, "second")
        self.assertEqual(pkg2.license, "MIT")
        self.assertEqual(
            pkg2.installdepends,
            {
                Dependency(DependencyKind.HOST, "dep"),
            },
        )
        self.assertEqual(pkg2.conflicts, set())
        self.assertEqual(pkg2.replaces, set())
        self.assertEqual(
            pkg2.package,
            """\
declare -a flags=()
declare -- timestamp=2021-08-01T10:27Z
declare -a source=([0]=https://example.org/toltec/pkg/release-4.3.2.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -- maintainer='None <none@example.org>'
declare -- image=base:v2.1
declare -- arch=rmall
declare -- pkgname=pkg2
declare -- pkgver=5:4.3.2-1
declare -- pkgdesc='Second package'
declare -- url=https://example.org/toltec/pkg/pkg2
declare -- section=second
declare -- license=MIT
declare -a installdepends=([0]=dep)
declare -a conflicts=()
declare -a replaces=()
declare -- _upver=4.3.2


    echo "Second package function"
""",
        )

        pkg3 = recipe.packages["pkg3"]

        self.assertEqual(pkg3.name, "pkg3")
        self.assertEqual(pkg3.parent, recipe)
        self.assertEqual(pkg3.version, Version(5, "4.3.2", "1"))
        self.assertEqual(pkg3.desc, "Third package")
        self.assertEqual(pkg3.url, "https://example.org/toltec/pkg/pkg3")
        self.assertEqual(pkg3.section, "third")
        self.assertEqual(pkg3.license, "GPL-3.0")
        self.assertEqual(
            pkg3.installdepends,
            {
                Dependency(DependencyKind.HOST, "dep"),
                Dependency(DependencyKind.HOST, "other-dep"),
            },
        )
        self.assertEqual(pkg3.conflicts, set())
        self.assertEqual(pkg3.replaces, set())
        self.assertEqual(
            pkg3.package,
            """\
declare -a flags=()
declare -- timestamp=2021-08-01T10:27Z
declare -a source=([0]=https://example.org/toltec/pkg/release-4.3.2.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -- maintainer='None <none@example.org>'
declare -- image=base:v2.1
declare -- arch=rmall
declare -- pkgname=pkg3
declare -- pkgver=5:4.3.2-1
declare -- pkgdesc='Third package'
declare -- url=https://example.org/toltec/pkg/pkg3
declare -- section=third
declare -- license=GPL-3.0
declare -a installdepends=([0]=dep [1]=other-dep)
declare -a conflicts=()
declare -a replaces=()
declare -- _upver=4.3.2


    echo "Third package function"
""",
        )
