# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""
Parse versions and dependency specifications.

Syntax and comparison rules for version numbers and comparison operators are
taken from Debian’s. See:

* <https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-version>
* <https://www.debian.org/doc/debian-policy/ch-relationships.html>
"""

import re
from functools import total_ordering
from enum import Enum
from typing import Optional, Callable

# Characters permitted in the upstream part of a version number
_UPSTREAM_CHARS = "A-Za-z0-9.+~-"
_UPSTREAM_REGEX = re.compile(f"^[{_UPSTREAM_CHARS}]*$")

# Characters permitted in the revision part of a version number
_REVISION_CHARS = "A-Za-z0-9.+~"
_REVISION_REGEX = re.compile(f"^[{_REVISION_CHARS}]*$")

# Characters making up a version comparator
_COMPARATOR_CHARS = re.compile("[<>=]+")

# Regex used to find digit and non-digit chars
_DIGIT_REGEX = re.compile("[0-9]")
_NON_DIGIT_REGEX = re.compile("[^0-9]")

# Sorting key used for non-digit version parts
_ALPHA_SORT_KEY = (
    (
        "~",  # ~ sorts lower than anything, even empty parts
        None,
    )
    + tuple(chr(letter) for letter in range(ord("A"), ord("Z") + 1))
    + tuple(chr(letter) for letter in range(ord("a"), ord("z") + 1))
    + (
        "+",
        "-",
        ".",
    )
)


def _find_digit(string: str) -> int:
    """
    Find the index of the first digit char in a string, or return the
    length of the string if there is none.
    """
    matches = _DIGIT_REGEX.search(string)
    return len(string) if not matches else matches.start()


def _find_non_digit(string: str) -> int:
    """
    Find the index of the first non-digit char in a string, or return the
    length of the string if there is none.
    """
    matches = _NON_DIGIT_REGEX.search(string)
    return len(string) if not matches else matches.start()


def _compare_version_parts(left: str, right: str) -> bool:
    """
    Compare two parts of a version string according to Debian version
    sorting rules.
    :returns: true if and only if `left` is strictly lower than `right`
    """

    def split(
        string: str, index_finder: Callable[[str], int]
    ) -> tuple[str, str]:
        index = index_finder(string)
        return string[:index], string[index:]

    def map_alpha(string: str, length: int) -> tuple[int, ...]:
        return tuple(
            _ALPHA_SORT_KEY.index(string[i])
            if i in range(len(string))
            else _ALPHA_SORT_KEY.index(None)
            for i in range(length)
        )

    # Split the strings into alternating non-digit parts and numeric parts,
    # compare non-digit parts using _ALPHA_SORT_KEY and numeric parts as
    # integers, stop at the first non-equal part
    while left or right:
        left_alpha, left = split(left, _find_digit)
        right_alpha, right = split(right, _find_digit)

        max_len = max(len(left_alpha), len(right_alpha))
        left_map = map_alpha(left_alpha, max_len)
        right_map = map_alpha(right_alpha, max_len)

        if left_map != right_map:
            return left_map < right_map

        left_digit, left = split(left, _find_non_digit)
        right_digit, right = split(right, _find_non_digit)

        left_numeric = int(left_digit)
        right_numeric = int(right_digit)

        if left_numeric != right_numeric:
            return left_numeric < right_numeric

    return False


class VersionComparator(Enum):
    """Operators used to compare two version numbers."""

    LOWER_THAN = "<<"
    LOWER_THAN_OR_EQUAL = "<="
    EQUAL = "="
    GREATER_THAN_OR_EQUAL = ">="
    GREATER_THAN = ">>"


class InvalidVersionError(Exception):
    """Raised when parsing of an invalid version is attempted."""


@total_ordering
class Version:
    """
    Parse package versions.

    for details about the format and the comparison rules.
    """

    def __init__(self, epoch: int, upstream: str, revision: str):
        self.upstream = upstream
        self.revision = revision
        self.epoch = epoch

        if epoch < 0:
            raise InvalidVersionError(
                f"Invalid epoch '{epoch}', only non-negative values "
                "are allowed"
            )

        if not upstream:
            raise InvalidVersionError("Upstream version cannot be empty")

        if _UPSTREAM_REGEX.fullmatch(upstream) is None:
            raise InvalidVersionError(
                f"Invalid chars in upstream version '{upstream}', allowed "
                f"chars are {_UPSTREAM_CHARS}"
            )

        if not revision:
            raise InvalidVersionError("Revision cannot be empty")

        if _REVISION_REGEX.fullmatch(revision) is None:
            raise InvalidVersionError(
                f"Invalid chars in revision '{revision}' allowed chars "
                f"are {_REVISION_CHARS}"
            )

        self._original: Optional[str] = None

    @staticmethod
    def parse(version: str) -> "Version":
        """Parse a version number."""
        original = version
        first_colon = version.find(":")

        if first_colon == -1:
            epoch = 0
        else:
            epoch_text = version[:first_colon]
            version = version[first_colon + 1 :]

            try:
                epoch = int(epoch_text)
            except ValueError as err:
                raise InvalidVersionError(
                    f"Invalid epoch '{epoch_text}', must be numeric"
                ) from err

        last_dash = version.rfind("-")

        if last_dash == -1:
            revision = "0"
        else:
            revision = version[last_dash + 1 :]
            version = version[:last_dash]

        upstream = version

        result = Version(epoch, upstream, revision)
        result._original = original  # pylint:disable=protected-access
        return result

    def __str__(self) -> str:
        if self._original is not None:
            # Use the original parsed version string
            return self._original

        epoch = "" if self.epoch == 0 else f"{self.epoch}:"
        revision = (
            ""
            if self.revision == "0" and "-" not in self.upstream
            else f"-{self.revision}"
        )

        return f"{epoch}{self.upstream}{revision}"

    def __repr__(self) -> str:
        return f"Version(upstream={repr(self.upstream)}, \
revision={repr(self.revision)}, epoch={repr(self.epoch)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        return (
            self.epoch == other.epoch
            and self.upstream == other.upstream
            and self.revision == other.revision
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented

        if self.epoch != other.epoch:
            return self.epoch < other.epoch

        if self.upstream != other.upstream:
            return _compare_version_parts(self.upstream, other.upstream)

        return _compare_version_parts(self.revision, other.revision)

    def __hash__(self) -> int:
        return hash((self.epoch, self.upstream, self.revision))


class DependencyKind(Enum):
    """Kinds of dependencies that may be requested by a package."""

    # Dependency installed in the system used to build a package
    # (e.g., a Debian package)
    BUILD = "build"
    # Dependency installed alongside a package
    # (e.g., another Entware or Toltec package)
    HOST = "host"


class InvalidDependencyError(Exception):
    """Raised when parsing an invalid dependency specification."""


class Dependency:
    """
    Parse version-constrained dependencies.

    Toltec dependencies are declared using the following format:

        [host:|build:]package[(<<|<=|=|=>|>>)version]

    Dependencies of a package that start with `build:` correspond to packages
    that must be installed in the build system. Dependencies that start with
    `host:` or do not have a prefix correspond to packages that must be
    installed alongside the built package, either in the host sysroot when
    building the package, or in the target device when using it.
    """

    def __init__(
        self,
        kind: DependencyKind,
        package: str,
        version_comparator: VersionComparator = VersionComparator.EQUAL,
        version: Optional[Version] = None,
    ):
        self.kind = kind
        self.package = package
        self.version_comparator = version_comparator
        self.version = version

        self._original: Optional[str] = None

    @staticmethod
    def parse(dependency: str) -> "Dependency":
        """Parse a dependency specification."""
        original = dependency
        comp_match = _COMPARATOR_CHARS.search(dependency)

        if comp_match is None:
            version_comparator = VersionComparator.EQUAL
            version = None
        else:
            comparator_str = comp_match.group(0)
            comp_char = comp_match.start()

            for enum_comparator in VersionComparator:
                if enum_comparator.value == comparator_str:
                    version_comparator = enum_comparator
                    version = Version.parse(dependency[comp_match.end() :])
                    dependency = dependency[: comp_match.start()]
                    break
            else:
                raise InvalidDependencyError(
                    f"Invalid version comparator '{comp_char}', valid types "
                    "are "
                    + ",".join(
                        f"'{enum_comparator.value}'"
                        for enum_comparator in VersionComparator
                    )
                )

        colon = dependency.find(":")

        if colon == -1:
            kind = DependencyKind.HOST
            package = dependency
        else:
            dep_kind_str = dependency[:colon]

            for enum_kind in DependencyKind:
                if enum_kind.value == dep_kind_str:
                    kind = enum_kind
                    package = dependency[colon + 1 :]
                    break
            else:
                raise InvalidDependencyError(
                    f"Unknown dependency type '{dep_kind_str}', valid types "
                    "are "
                    + ",".join(
                        f"'{enum_kind.value}'" for enum_kind in DependencyKind
                    )
                )

        result = Dependency(kind, package, version_comparator, version)
        result._original = original  # pylint:disable=protected-access
        return result

    def match(self, version: Version) -> bool:
        """Check whether a given version fulfills this dependency."""
        if self.version is None:
            return True

        if self.version_comparator == VersionComparator.EQUAL:
            return version == self.version

        if self.version_comparator == VersionComparator.LOWER_THAN:
            return version < self.version

        if self.version_comparator == VersionComparator.LOWER_THAN_OR_EQUAL:
            return version <= self.version

        if self.version_comparator == VersionComparator.GREATER_THAN:
            return version > self.version

        # self.version_comparator == VersionComparator.GREATER_THAN_OR_EQUAL:
        return version >= self.version

    def to_debian(self) -> str:
        """Convert a dependency specification to the Debian format."""
        if self.version is None:
            return self.package

        return f"{self.package} ({self.version_comparator.value} \
{self.version})"

    def __str__(self) -> str:
        if self._original is not None:
            # Use the original parsed dependency specification
            return self._original

        kind = "build:" if self.kind == DependencyKind.BUILD else "host:"

        if self.version is None:
            return f"{kind}{self.package}"

        return f"{kind}{self.package}{self.version_comparator.value}\
{self.version}"

    def __repr__(self) -> str:
        return f"Dependency(kind={repr(self.kind)}, \
package={repr(self.package)}, \
version_comparator={repr(self.version_comparator)}, \
version={repr(self.version)})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Dependency):
            return (
                self.kind == other.kind
                and self.package == other.package
                and self.version_comparator == other.version_comparator
                and self.version == other.version
            )

        return False

    def __hash__(self) -> int:
        return hash(
            (self.kind, self.package, self.version_comparator, self.version)
        )
