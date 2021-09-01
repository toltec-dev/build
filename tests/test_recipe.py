# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

import unittest
import textwrap
from datetime import datetime
from toltec.recipe import Package, Recipe
from toltec.version import (
    Version,
    Dependency,
    DependencyKind,
    VersionComparator,
)


class TestRecipe(unittest.TestCase):
    def test_derived_fields(self) -> None:
        rec = Recipe(
            path="test",
            timestamp=datetime.now(),
            sources=set(),
            makedepends=set(),
            maintainer="Test <test@example.com>",
            image="",
            arch="armv7-3.2",
            flags=[],
            prepare="",
            build="",
            packages={},
        )

        pkg = Package(
            name="test",
            parent=rec,
            version=Version(42, "12.1", "8"),
            desc="Test package",
            url="https://example.com/toltec/test",
            section="misc",
            license="MIT",
            installdepends={
                Dependency(
                    DependencyKind.HOST,
                    "test-dep",
                    VersionComparator.EQUAL,
                    Version(42, "1.0.0", "8"),
                ),
                Dependency(
                    DependencyKind.HOST,
                    "aaaaaaaa",
                    VersionComparator.GREATER_THAN_OR_EQUAL,
                    Version(0, "1.0.0", "1"),
                ),
            },
            recommends={Dependency(DependencyKind.HOST, "recommended")},
            optdepends={Dependency(DependencyKind.HOST, "optdep")},
            conflicts={Dependency(DependencyKind.HOST, "conflict")},
            replaces={Dependency(DependencyKind.HOST, "replaced")},
            provides={Dependency(DependencyKind.HOST, "provided")},
            package="",
            preinstall="",
            configure="",
            preupgrade="",
            postupgrade="",
            preremove="",
            postremove="",
        )

        self.assertEqual(pkg.pkgid(), "test_42_12.1-8_armv7-3.2")
        self.assertEqual(
            pkg.filename(), "armv7-3.2/test_42_12.1-8_armv7-3.2.ipk"
        )
        self.assertEqual(
            pkg.control_fields(),
            textwrap.dedent(
                """\
                Package: test
                Description: Test package
                Homepage: https://example.com/toltec/test
                Version: 42:12.1-8
                Section: misc
                Maintainer: Test <test@example.com>
                License: MIT
                Architecture: armv7-3.2
                Depends: aaaaaaaa (>= 1.0.0-1), test-dep (= 42:1.0.0-8)
                Recommends: recommended
                Suggests: optdep
                Conflicts: conflict
                Replaces: replaced
                Provides: provided
                """
            ),
        )
