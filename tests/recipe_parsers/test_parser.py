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


class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        self.dir_handle = TemporaryDirectory()
        self.dir = self.dir_handle.name

    def tearDown(self) -> None:
        self.dir = None
        self.dir_handle.cleanup()

    def test_basic_recipe(self) -> None:
        """Check that basic fields are parsed."""
        rec_path = path.join(self.dir, "basic-recipe")
        os.makedirs(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(basic-recipe)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/basic-recipe
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

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
        self.assertEqual(recipe.preparedepends, set())
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
declare -a preparedepends=()
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
        self.assertEqual(package.recommends, set())
        self.assertEqual(package.optdepends, set())
        self.assertEqual(package.conflicts, set())
        self.assertEqual(package.replaces, set())
        self.assertEqual(package.provides, set())
        self.assertEqual(
            package.package,
            """\
declare -a flags=()
declare -- timestamp=2021-07-31T20:44Z
declare -a source=([0]=https://example.org/toltec/basic-recipe/release-42.0.zip)
declare -a sha256sums=([0]=SKIP)
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
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
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()


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

    def test_dependencies(self):
        """Check that dependency fields are parsed (depends, recommends, ...)"""
        rec_path = path.join(self.dir, "dependencies")
        os.makedirs(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(dependencies)
pkgdesc="Test for package dependency declarations"
url=https://example.org/toltec/dependencies
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT
installdepends=(aa bb cc=0.1 "dd>=2.0" "ee>=1.4" "ee<<2.0")
recommends=(ff gg hh)
optdepends=(ii jj kk)
conflicts=(ll mm nn)
replaces=(ll mm nn)
provides=(oo=1.0)

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

        package = parse_recipe(rec_path)["rmall"].packages["dependencies"]

        self.assertEqual(package.name, "dependencies")
        self.assertEqual(
            package.installdepends,
            {
                Dependency(DependencyKind.HOST, "aa"),
                Dependency(DependencyKind.HOST, "bb"),
                Dependency(
                    DependencyKind.HOST,
                    "cc",
                    VersionComparator.EQUAL,
                    Version(0, "0.1", "0"),
                ),
                Dependency(
                    DependencyKind.HOST,
                    "dd",
                    VersionComparator.GREATER_THAN_OR_EQUAL,
                    Version(0, "2.0", "0"),
                ),
                Dependency(
                    DependencyKind.HOST,
                    "ee",
                    VersionComparator.GREATER_THAN_OR_EQUAL,
                    Version(0, "1.4", "0"),
                ),
                Dependency(
                    DependencyKind.HOST,
                    "ee",
                    VersionComparator.LOWER_THAN,
                    Version(0, "2.0", "0"),
                ),
            },
        )
        self.assertEqual(
            package.recommends,
            {
                Dependency(DependencyKind.HOST, "ff"),
                Dependency(DependencyKind.HOST, "gg"),
                Dependency(DependencyKind.HOST, "hh"),
            },
        )
        self.assertEqual(
            package.optdepends,
            {
                Dependency(DependencyKind.HOST, "ii"),
                Dependency(DependencyKind.HOST, "jj"),
                Dependency(DependencyKind.HOST, "kk"),
            },
        )
        self.assertEqual(
            package.conflicts,
            {
                Dependency(DependencyKind.HOST, "ll"),
                Dependency(DependencyKind.HOST, "mm"),
                Dependency(DependencyKind.HOST, "nn"),
            },
        )
        self.assertEqual(
            package.replaces,
            {
                Dependency(DependencyKind.HOST, "ll"),
                Dependency(DependencyKind.HOST, "mm"),
                Dependency(DependencyKind.HOST, "nn"),
            },
        )
        self.assertEqual(
            package.provides,
            {
                Dependency(
                    DependencyKind.HOST,
                    "oo",
                    VersionComparator.EQUAL,
                    Version(0, "1.0", "0"),
                ),
            },
        )
        self.assertEqual(
            package.control_fields(),
            """\
Package: dependencies
Description: Test for package dependency declarations
Homepage: https://example.org/toltec/dependencies
Version: 42.0-1
Section: test
Maintainer: None <none@example.org>
License: MIT
Architecture: rmall
Depends: aa, bb, cc (= 0.1), dd (>= 2.0), ee (<< 2.0), ee (>= 1.4)
Recommends: ff, gg, hh
Suggests: ii, jj, kk
Conflicts: ll, mm, nn
Replaces: ll, mm, nn
Provides: oo (= 1.0)
""",
        )

    def test_split_packages(self):
        """Check that recipes defining several packages are parsed."""
        rec_path = path.join(self.dir, "split-packages")
        os.makedirs(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(pkg1 pkg2 pkg3)
timestamp=2021-08-01T10:27Z
maintainer="None <none@example.org>"
installdepends=(dep)
pkgver=5:4.3.2-1
license=MIT

image=base:v2.1
_upver="${pkgver%-*}"
_upver="${_upver#*:}"
source=("https://example.org/toltec/pkg/release-$_upver.zip")
sha256sums=(SKIP)

prepare() {
    echo "Prepare function"
}

build() {
    echo "Build function"
}

pkg1() {
    pkgdesc="First package"
    url="https://example.org/toltec/pkg/$pkgname"
    section="first"

    package() {
        echo "First package function"
    }
}

pkg2() {
    pkgdesc="Second package"
    url="https://example.org/toltec/pkg/$pkgname"
    section="second"

    package() {
        echo "Second package function"
    }
}

pkg3() {
    pkgdesc="Third package"
    url="https://example.org/toltec/pkg/$pkgname"
    section="third"
    license=GPL-3.0
    installdepends+=(other-dep)

    package() {
        echo "Third package function"
    }
}
"""
            )

        recipes = parse_recipe(rec_path)
        self.assertEqual(list(recipes.keys()), ["rmall"])
        recipe = recipes["rmall"]

        self.assertEqual(recipe.path, rec_path)
        self.assertEqual(recipe.makedepends, set())
        self.assertEqual(recipe.preparedepends, set())
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
declare -a preparedepends=()
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
declare -a preparedepends=()
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

        self.assertEqual(list(recipe.packages.keys()), ["pkg1", "pkg2", "pkg3"])
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
declare -a preparedepends=()
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
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()
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
declare -a preparedepends=()
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
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()
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
declare -a preparedepends=()
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
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()
declare -- _upver=4.3.2


    echo "Third package function"
""",
        )

    def test_split_archs(self):
        """Check that recipes supporting multiple architectures are parsed."""
        rec_path = path.join(self.dir, "split-archs")
        os.makedirs(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(test-archs-part1 test-archs-part2)
pkgdesc="Dummy package for testing the arch separation feature"
url=https://example.org/test-archs
url_rm2=https://example.org/test-archs-rm2
archs=(rm1 rm2)
pkgver_rm1=0.0.0-1
pkgver_rm2=0.0.0-2
timestamp=2020-08-20T12:28Z
section="math"
section_rm2="math-rm2"
maintainer="Mattéo Delabre <spam@delab.re>"
maintainer_rm2="None <none@example.com>"
license=GPL-3.0-or-later
license_rm2=MIT
installdepends=(some-package)
installdepends_rm2=(rm2-only-dep)

image=qt:v1.1
image_rm2=qt:v1.3

build() {
    echo "Building for $arch"
}

_configure() {
    echo "This package was built for $arch"
}

test-archs-part1() {
    pkgdesc="$arch $pkgname - test arch separation"

    package() {
        echo "Package part 1"
    }

    configure() {
        echo "This is $pkgname"
        _configure
    }
}

test-archs-part2() {
    pkgdesc="$arch $pkgname - test arch separation"

    package() {
        echo "Package part 2"
    }

    configure() {
        echo "This is $pkgname"
        _configure
    }
}
"""
            )

        recipes = parse_recipe(rec_path)
        self.assertEqual(list(recipes.keys()), ["rm1", "rm2"])

        rm1 = recipes["rm1"]
        self.assertEqual(rm1.path, rec_path)
        self.assertEqual(
            rm1.timestamp, datetime(2020, 8, 20, 12, 28, 0, 0, timezone.utc)
        )
        self.assertEqual(rm1.sources, set())
        self.assertEqual(rm1.makedepends, set())
        self.assertEqual(rm1.maintainer, "Mattéo Delabre <spam@delab.re>")
        self.assertEqual(rm1.image, "qt:v1.1")
        self.assertEqual(rm1.arch, "rm1")
        self.assertEqual(rm1.flags, [])
        self.assertEqual(rm1.prepare, "")
        self.assertEqual(
            rm1.build,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='Mattéo Delabre <spam@delab.re>'
declare -- image=qt:v1.1
declare -- arch=rm1
declare -a installdepends=([0]=some-package)
declare -- license=GPL-3.0-or-later
declare -- pkgdesc='Dummy package for testing the arch separation feature'
declare -- section=math
declare -- url=https://example.org/test-archs
declare -- pkgver=0.0.0-1

_configure() {

    echo "This package was built for $arch"

}

    echo "Building for $arch"
""",
        )

        self.assertEqual(
            list(rm1.packages.keys()),
            [
                "test-archs-part1",
                "test-archs-part2",
            ],
        )

        part1 = rm1.packages["test-archs-part1"]
        self.assertEqual(part1.name, "test-archs-part1")
        self.assertEqual(part1.parent, rm1)
        self.assertEqual(part1.version, Version(0, "0.0.0", "1"))
        self.assertEqual(
            part1.desc,
            "rm1 test-archs-part1 - test arch separation",
        )
        self.assertEqual(part1.url, "https://example.org/test-archs")
        self.assertEqual(part1.section, "math")
        self.assertEqual(part1.license, "GPL-3.0-or-later")
        self.assertEqual(
            part1.installdepends,
            {Dependency(DependencyKind.HOST, "some-package")},
        )
        self.assertEqual(part1.conflicts, set())
        self.assertEqual(part1.replaces, set())
        self.assertEqual(
            part1.package,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='Mattéo Delabre <spam@delab.re>'
declare -- image=qt:v1.1
declare -- arch=rm1
declare -- pkgname=test-archs-part1
declare -- pkgver=0.0.0-1
declare -- pkgdesc='rm1 test-archs-part1 - test arch separation'
declare -- url=https://example.org/test-archs
declare -- section=math
declare -- license=GPL-3.0-or-later
declare -a installdepends=([0]=some-package)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "Package part 1"
""",
        )
        self.assertEqual(part1.preinstall, "")
        self.assertEqual(
            part1.configure,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='Mattéo Delabre <spam@delab.re>'
declare -- image=qt:v1.1
declare -- arch=rm1
declare -- pkgname=test-archs-part1
declare -- pkgver=0.0.0-1
declare -- pkgdesc='rm1 test-archs-part1 - test arch separation'
declare -- url=https://example.org/test-archs
declare -- section=math
declare -- license=GPL-3.0-or-later
declare -a installdepends=([0]=some-package)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "This is $pkgname";
    _configure
""",
        )
        self.assertEqual(part1.preupgrade, "")
        self.assertEqual(part1.postupgrade, "")
        self.assertEqual(part1.preremove, "")
        self.assertEqual(part1.postremove, "")

        part2 = rm1.packages["test-archs-part2"]
        self.assertEqual(part2.name, "test-archs-part2")
        self.assertEqual(part2.parent, rm1)
        self.assertEqual(part2.version, Version(0, "0.0.0", "1"))
        self.assertEqual(
            part2.desc,
            "rm1 test-archs-part2 - test arch separation",
        )
        self.assertEqual(part2.url, "https://example.org/test-archs")
        self.assertEqual(part2.section, "math")
        self.assertEqual(part2.license, "GPL-3.0-or-later")
        self.assertEqual(
            part2.installdepends,
            {Dependency(DependencyKind.HOST, "some-package")},
        )
        self.assertEqual(part2.conflicts, set())
        self.assertEqual(part2.replaces, set())
        self.assertEqual(
            part2.package,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='Mattéo Delabre <spam@delab.re>'
declare -- image=qt:v1.1
declare -- arch=rm1
declare -- pkgname=test-archs-part2
declare -- pkgver=0.0.0-1
declare -- pkgdesc='rm1 test-archs-part2 - test arch separation'
declare -- url=https://example.org/test-archs
declare -- section=math
declare -- license=GPL-3.0-or-later
declare -a installdepends=([0]=some-package)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "Package part 2"
""",
        )
        self.assertEqual(part2.preinstall, "")
        self.assertEqual(
            part2.configure,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='Mattéo Delabre <spam@delab.re>'
declare -- image=qt:v1.1
declare -- arch=rm1
declare -- pkgname=test-archs-part2
declare -- pkgver=0.0.0-1
declare -- pkgdesc='rm1 test-archs-part2 - test arch separation'
declare -- url=https://example.org/test-archs
declare -- section=math
declare -- license=GPL-3.0-or-later
declare -a installdepends=([0]=some-package)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "This is $pkgname";
    _configure
""",
        )
        self.assertEqual(part2.preupgrade, "")
        self.assertEqual(part2.postupgrade, "")
        self.assertEqual(part2.preremove, "")
        self.assertEqual(part2.postremove, "")

        rm2 = recipes["rm2"]
        self.assertEqual(rm2.path, rec_path)
        self.assertEqual(
            rm2.timestamp, datetime(2020, 8, 20, 12, 28, 0, 0, timezone.utc)
        )
        self.assertEqual(rm2.sources, set())
        self.assertEqual(rm2.makedepends, set())
        self.assertEqual(rm2.preparedepends, set())
        self.assertEqual(rm2.maintainer, "None <none@example.com>")
        self.assertEqual(rm2.image, "qt:v1.3")
        self.assertEqual(rm2.arch, "rm2")
        self.assertEqual(rm2.flags, [])
        self.assertEqual(rm2.prepare, "")
        self.assertEqual(
            rm2.build,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='None <none@example.com>'
declare -- image=qt:v1.3
declare -- arch=rm2
declare -a installdepends=([0]=some-package [1]=rm2-only-dep)
declare -- license=MIT
declare -- pkgdesc='Dummy package for testing the arch separation feature'
declare -- section=math-rm2
declare -- url=https://example.org/test-archs-rm2
declare -- pkgver=0.0.0-2

_configure() {

    echo "This package was built for $arch"

}

    echo "Building for $arch"
""",
        )

        self.assertEqual(
            list(rm2.packages.keys()),
            [
                "test-archs-part1",
                "test-archs-part2",
            ],
        )

        part1 = rm2.packages["test-archs-part1"]
        self.assertEqual(part1.name, "test-archs-part1")
        self.assertEqual(part1.parent, rm2)
        self.assertEqual(part1.version, Version(0, "0.0.0", "2"))
        self.assertEqual(
            part1.desc,
            "rm2 test-archs-part1 - test arch separation",
        )
        self.assertEqual(part1.url, "https://example.org/test-archs-rm2")
        self.assertEqual(part1.section, "math-rm2")
        self.assertEqual(part1.license, "MIT")
        self.assertEqual(
            part1.installdepends,
            {
                Dependency(DependencyKind.HOST, "some-package"),
                Dependency(DependencyKind.HOST, "rm2-only-dep"),
            },
        )
        self.assertEqual(part1.conflicts, set())
        self.assertEqual(part1.replaces, set())
        self.assertEqual(
            part1.package,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='None <none@example.com>'
declare -- image=qt:v1.3
declare -- arch=rm2
declare -- pkgname=test-archs-part1
declare -- pkgver=0.0.0-2
declare -- pkgdesc='rm2 test-archs-part1 - test arch separation'
declare -- url=https://example.org/test-archs-rm2
declare -- section=math-rm2
declare -- license=MIT
declare -a installdepends=([0]=some-package [1]=rm2-only-dep)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "Package part 1"
""",
        )
        self.assertEqual(part1.preinstall, "")
        self.assertEqual(
            part1.configure,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='None <none@example.com>'
declare -- image=qt:v1.3
declare -- arch=rm2
declare -- pkgname=test-archs-part1
declare -- pkgver=0.0.0-2
declare -- pkgdesc='rm2 test-archs-part1 - test arch separation'
declare -- url=https://example.org/test-archs-rm2
declare -- section=math-rm2
declare -- license=MIT
declare -a installdepends=([0]=some-package [1]=rm2-only-dep)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "This is $pkgname";
    _configure
""",
        )
        self.assertEqual(part1.preupgrade, "")
        self.assertEqual(part1.postupgrade, "")
        self.assertEqual(part1.preremove, "")
        self.assertEqual(part1.postremove, "")

        part2 = rm2.packages["test-archs-part2"]
        self.assertEqual(part2.name, "test-archs-part2")
        self.assertEqual(part2.parent, rm2)
        self.assertEqual(part2.version, Version(0, "0.0.0", "2"))
        self.assertEqual(
            part2.desc,
            "rm2 test-archs-part2 - test arch separation",
        )
        self.assertEqual(part2.url, "https://example.org/test-archs-rm2")
        self.assertEqual(part2.section, "math-rm2")
        self.assertEqual(part2.license, "MIT")
        self.assertEqual(
            part2.installdepends,
            {
                Dependency(DependencyKind.HOST, "some-package"),
                Dependency(DependencyKind.HOST, "rm2-only-dep"),
            },
        )
        self.assertEqual(part2.conflicts, set())
        self.assertEqual(part2.replaces, set())
        self.assertEqual(
            part2.package,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='None <none@example.com>'
declare -- image=qt:v1.3
declare -- arch=rm2
declare -- pkgname=test-archs-part2
declare -- pkgver=0.0.0-2
declare -- pkgdesc='rm2 test-archs-part2 - test arch separation'
declare -- url=https://example.org/test-archs-rm2
declare -- section=math-rm2
declare -- license=MIT
declare -a installdepends=([0]=some-package [1]=rm2-only-dep)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "Package part 2"
""",
        )
        self.assertEqual(part2.preinstall, "")
        self.assertEqual(
            part2.configure,
            """\
declare -a flags=()
declare -- timestamp=2020-08-20T12:28Z
declare -a source=()
declare -a sha256sums=()
declare -a noextract=()
declare -a makedepends=()
declare -a preparedepends=()
declare -- maintainer='None <none@example.com>'
declare -- image=qt:v1.3
declare -- arch=rm2
declare -- pkgname=test-archs-part2
declare -- pkgver=0.0.0-2
declare -- pkgdesc='rm2 test-archs-part2 - test arch separation'
declare -- url=https://example.org/test-archs-rm2
declare -- section=math-rm2
declare -- license=MIT
declare -a installdepends=([0]=some-package [1]=rm2-only-dep)
declare -a recommends=()
declare -a optdepends=()
declare -a conflicts=()
declare -a replaces=()
declare -a provides=()

_configure() {

    echo "This package was built for $arch"

}

    echo "This is $pkgname";
    _configure
""",
        )
        self.assertEqual(part2.preupgrade, "")
        self.assertEqual(part2.postupgrade, "")
        self.assertEqual(part2.preremove, "")
        self.assertEqual(part2.postremove, "")

    def test_errors(self) -> None:
        """Check error messages raised when invalid recipes are parsed."""
        rec_path = path.join(self.dir, "errors")
        os.makedirs(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(bash-syntax-error
"""
            )

        with self.assertRaisesRegex(
            ScriptError,
            re.escape(
                """Bash error
bash: line 2: unexpected EOF while looking for matching `)'"""
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(missing-timestamp)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/missing-timestamp
pkgver=42.0-1
section="test"
maintainer="None <none@example.org>"
license=MIT

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

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(f"{rec_path}: Missing required field 'timestamp'"),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(wrong-type)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/wrong-type
pkgver=(42.0-1)
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

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

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Field 'pkgver' must be a string, got a \
list"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(wrong-type-2)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/wrong-type-2
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

image=base:v2.1
source="https://example.org/toltec/${pkgnames[0]}/release-${pkgver%-*}.zip"
sha256sums=SKIP

build() {
    echo "Build function"
}

package() {
    echo "Package function"
}
"""
            )

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Field 'source' must be an indexed array, \
got a str"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(missing-image)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/missing-image
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

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

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Missing image declaration for a recipe \
which has a build() step"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(missing-build)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/missing-build
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

image=base:v2.1
source=("https://example.org/toltec/${pkgnames[0]}/release-${pkgver%-*}.zip")
sha256sums=(SKIP)

package() {
    echo "Package function"
}
"""
            )

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Missing build() function for a recipe \
which declares a build image"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(missing-pkg-func-1 missing-pkg-func-2)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/missing-pkg-func
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

image=base:v2.1
source=("https://example.org/toltec/${pkgnames[0]}/release-${pkgver%-*}.zip")
sha256sums=(SKIP)

build() {
    echo "Build function"
}

missing-pkg-func-1() {
    package() {
        echo "Package function"
    }
}
"""
            )

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Missing required function \
missing-pkg-func-2() for corresponding package"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(wrong-timestamp-format)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/wrong-timestamp-format
pkgver=42.0-1
timestamp=2021/07/31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

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

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Field 'timestamp' does not contain a \
valid ISO-8601 date"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(mismatched-sources-checksums)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/mismatched-sources-checksums
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

image=base:v2.1
source=("https://example.org/toltec/${pkgnames[0]}/release-${pkgver%-*}.zip")
sha256sums=(SKIP SKIP SKIP)

build() {
    echo "Build function"
}

package() {
    echo "Package function"
}
"""
            )

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Expected the same number of sources and \
checksums, got 1 source(s) and 3 checksum(s)"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(invalid-version)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/invalid-version
pkgver=//42.0//-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

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

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Failed to parse version number: '//42.0//-1'"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(invalid-dependency)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/invalid-dependency
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT
installdepends=("package (=0.1.2-5)")

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

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Failed to parse dependency: 'package (=0.1.2-5)'"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(invalid-dep-type)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/invalid-dep-type
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT
installdepends=(build:package)

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

        with self.assertRaisesRegex(
            RecipeError,
            re.escape(
                f"{rec_path}: Only host packages are supported in the \
'installdepends' field, cannot add dependency 'build:package'"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(unknown-fields)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/unknown-fields
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT
customfield=4

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

        with self.assertWarnsRegex(
            RecipeWarning,
            re.escape(
                f"{rec_path}: Unknown field 'customfield'. Make sure to \
prefix the names of custom fields with '_'"
            ),
        ):
            parse_recipe(rec_path)

        with open(path.join(rec_path, "package"), "w") as rec_def_file:
            rec_def_file.write(
                """
pkgnames=(unknown-funcs)
pkgdesc="A simple test for recipe parsing"
url=https://example.org/toltec/unknown-funcs
pkgver=42.0-1
timestamp=2021-07-31T20:44Z
section="test"
maintainer="None <none@example.org>"
license=MIT

image=base:v2.1
source=("https://example.org/toltec/${pkgnames[0]}/release-${pkgver%-*}.zip")
sha256sums=(SKIP)

customfunc() {
    echo "Custom function"
}

build() {
    echo "Build function"
}

package() {
    echo "Package function"
}
"""
            )

        with self.assertWarnsRegex(
            RecipeWarning,
            re.escape(
                f"{rec_path}: Unknown function 'customfunc'. Make sure to \
prefix the names of custom functions with '_'"
            ),
        ):
            parse_recipe(rec_path)
