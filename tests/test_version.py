# Copyright (c) 2022 The Toltec Contributors
# SPDX-License-Identifier: MIT

import unittest
from toltec.version import (
    Version,
    Dependency,
    DependencyKind,
    VersionComparator,
    InvalidVersionError,
    InvalidDependencyError,
)


class TestVersion(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(
            InvalidVersionError,
            msg="Invalid epoch '-1', only non-negative values are allowed",
        ):
            version = Version(-1, "test", "0")

        with self.assertRaises(
            InvalidVersionError,
            msg="Invalid chars in upstream version 't:est', allowed chars "
            "are A-Za-z0-9.+~-",
        ):
            version = Version(0, "t:est", "0")

        with self.assertRaises(
            InvalidVersionError,
            msg="Upstream version cannot be empty",
        ):
            version = Version(0, "", "0")

        with self.assertRaises(
            InvalidVersionError,
            msg="Invalid chars in revision '1-2-3', allowed chars are "
            "A-Za-z0-9.+~",
        ):
            version = Version(0, "test", "1-2-3")

        with self.assertRaises(
            InvalidVersionError,
            msg="Revision cannot be empty",
        ):
            version = Version(0, "test", "")

        version = Version(1, "test", "1")
        self.assertEqual(version.upstream, "test")
        self.assertEqual(version.revision, "1")
        self.assertEqual(version.epoch, 1)

    def test_parse(self):
        valid_versions = (
            ("0.0.0-1", Version(0, "0.0.0", "1")),
            ("0.0.1-1", Version(0, "0.0.1", "1")),
            ("0.1.0-3", Version(0, "0.1.0", "3")),
            ("0.1.1", Version(0, "0.1.1", "0")),
            ("1.0-0", Version(0, "1.0", "0")),
            ("1.0.0", Version(0, "1.0.0", "0")),
            ("1-0-0", Version(0, "1-0", "0")),
            ("1:0.0.14-1", Version(1, "0.0.14", "1")),
            ("1.0.20210219-2", Version(0, "1.0.20210219", "2")),
            ("1.3.5-14", Version(0, "1.3.5", "14")),
            ("19.21-2", Version(0, "19.21", "2")),
            ("2.0.10-1", Version(0, "2.0.10", "1")),
            ("2020.11.08-2", Version(0, "2020.11.08", "2")),
        )

        for string, parsed in valid_versions:
            self.assertEqual(Version.parse(string), parsed)

        with self.assertRaises(
            InvalidVersionError,
            msg="Invalid epoch 'test', must be numeric",
        ):
            version = Version.parse("test:1.1")

        with self.assertRaises(
            InvalidVersionError,
            msg="Upstream version cannot be empty",
        ):
            version = Version.parse("0:-1")

    def test_compare(self):
        self.assertEqual(Version(0, "1.0", "1"), Version(0, "1.0", "1"))

        ordered_pairs = (
            (Version(0, "1.0", "1"), Version(1, "0.1", "1")),
            (Version(0, "1.0", "1"), Version(0, "1.0", "2")),
            (Version(0, "1.0", "2"), Version(0, "1.1", "1")),
            (Version(1, "1.0~~", "7"), Version(1, "1.0~~a", "1")),
            (Version(1, "1.0~~a", "7"), Version(1, "1.0~", "1")),
            (Version(1, "1.0~", "7"), Version(1, "1.0", "1")),
            (Version(1, "1.0", "7"), Version(1, "1.0a", "1")),
        )

        for lower, greater in ordered_pairs:
            self.assertTrue(lower < greater)
            self.assertTrue(lower <= greater)
            self.assertTrue(greater > lower)
            self.assertTrue(greater >= lower)
            self.assertFalse(greater < lower)
            self.assertFalse(greater <= lower)
            self.assertFalse(lower > greater)
            self.assertFalse(lower >= greater)


class TestDependency(unittest.TestCase):
    def test_init(self):
        version = Version(1, "0.1", "1")
        dep = Dependency(
            DependencyKind.BUILD,
            "test",
            VersionComparator.GREATER_THAN_OR_EQUAL,
            version,
        )
        self.assertEqual(dep.kind, DependencyKind.BUILD)
        self.assertEqual(dep.package, "test")
        self.assertEqual(
            dep.version_comparator,
            VersionComparator.GREATER_THAN_OR_EQUAL,
        )
        self.assertEqual(dep.version, version)

    def test_parse(self):
        valid_deps = (
            (
                "test",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.EQUAL,
                    None,
                ),
            ),
            (
                "host:test",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.EQUAL,
                    None,
                ),
            ),
            (
                "build:test",
                Dependency(
                    DependencyKind.BUILD,
                    "test",
                    VersionComparator.EQUAL,
                    None,
                ),
            ),
            (
                "test=0.1-1",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.EQUAL,
                    Version(0, "0.1", "1"),
                ),
            ),
            (
                "test<<0.1-1",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.LOWER_THAN,
                    Version(0, "0.1", "1"),
                ),
            ),
            (
                "test<=0.1-1",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.LOWER_THAN_OR_EQUAL,
                    Version(0, "0.1", "1"),
                ),
            ),
            (
                "test>>0.1-1",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.GREATER_THAN,
                    Version(0, "0.1", "1"),
                ),
            ),
            (
                "test>=0.1-1",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.GREATER_THAN_OR_EQUAL,
                    Version(0, "0.1", "1"),
                ),
            ),
            (
                "test=1:0.1-1",
                Dependency(
                    DependencyKind.HOST,
                    "test",
                    VersionComparator.EQUAL,
                    Version(1, "0.1", "1"),
                ),
            ),
            (
                "build:test=1:0.1-1",
                Dependency(
                    DependencyKind.BUILD,
                    "test",
                    VersionComparator.EQUAL,
                    Version(1, "0.1", "1"),
                ),
            ),
        )

        for string, parsed in valid_deps:
            self.assertEqual(Dependency.parse(string), parsed)

        with self.assertRaises(
            InvalidDependencyError,
            msg="Unknown dependency type 'invalid', valid types are "
            "'build', 'host'",
        ):
            dep = Dependency.parse("invalid:test")

        with self.assertRaises(
            InvalidDependencyError,
            msg="Invalid version comparator '<<>>', valid operators are "
            "'<<', '<=', '=', '>=', '>>'",
        ):
            dep = Dependency.parse("host:test<<>>0.1")

    def test_to_debian(self):
        converted_versions = (
            ("test", "test"),
            ("host:test", "test"),
            ("test=0.1-1", "test (= 0.1-1)"),
            ("test<<0.1-1", "test (<< 0.1-1)"),
            ("test<=0.1-1", "test (<= 0.1-1)"),
            ("test>>0.1-1", "test (>> 0.1-1)"),
            ("test>=0.1-1", "test (>= 0.1-1)"),
            ("test=1:0.1-1", "test (= 1:0.1-1)"),
        )

        for ours, debian in converted_versions:
            self.assertEqual(Dependency.parse(ours).to_debian(), debian)

    def test_match(self):
        matches = (
            ("test", "0.1", True),
            ("test", "0.1-0", True),
            ("test", "0:0.1-0", True),
            ("test", "0.1-1", True),
            ("test", "0.0", True),
            ("test", "1:0.0", True),
            ("test=0.1", "0.1", True),
            ("test=0.1", "0.1-0", True),
            ("test=0.1", "0:0.1-0", True),
            ("test=0.1", "0.1-1", False),
            ("test=0.1", "0.0", False),
            ("test=0.1", "1:0.0", False),
            ("test>=0.1", "0.1", True),
            ("test>=0.1", "0.1-0", True),
            ("test>=0.1", "0:0.1-0", True),
            ("test>=0.1", "0.1-1", True),
            ("test>=0.1", "0.0", False),
            ("test>=0.1", "1:0.0", True),
            ("test>>0.1", "0.1", False),
            ("test>>0.1", "0.1-0", False),
            ("test>>0.1", "0:0.1-0", False),
            ("test>>0.1", "0.1-1", True),
            ("test>>0.1", "0.0", False),
            ("test>>0.1", "1:0.0", True),
            ("test<=0.1", "0.1", True),
            ("test<=0.1", "0.1-0", True),
            ("test<=0.1", "0:0.1-0", True),
            ("test<=0.1", "0.1-1", False),
            ("test<=0.1", "0.0", True),
            ("test<=0.1", "1:0.0", False),
            ("test<<0.1", "0.1", False),
            ("test<<0.1", "0.1-0", False),
            ("test<<0.1", "0:0.1-0", False),
            ("test<<0.1", "0.1-1", False),
            ("test<<0.1", "0.0", True),
            ("test<<0.1", "1:0.0", False),
        )

        for dep, version, result in matches:
            self.assertEqual(
                Dependency.parse(dep).match(Version.parse(version)),
                result,
                f"match {dep} with {version} is {result}",
            )
