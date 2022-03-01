# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""
Package recipes.

A package is a final user-installable software archive. A recipe contains
the metadata and instructions necessary to build one or more related
packages (in the latter case, it is called a split package).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, NamedTuple, Set
import os
import textwrap
from .version import Version, Dependency


class RecipeError(Exception):
    """Raised when a recipe definition is malformed."""

    def __init__(self, path: str, message: str):
        super().__init__()
        self.path = path
        self.message = message

    def __repr__(self) -> str:
        return f"RecipeError(path={repr(self.path)}, \
message={repr(self.message)})"

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class RecipeWarning(Warning):
    """Raised for less serious issues in recipe definitions."""


# Set of variations of the same recipes that target different architectures
RecipeBundle = Dict[str, "Recipe"]


class Source(NamedTuple):
    """Source item needed to build a recipe."""

    # URL or local relative path to the source item
    url: str

    # SHA-256 checksum for validating the source integrity
    checksum: str

    # If true, do not attempt to extract this item after downloading
    noextract: bool


@dataclass
class Recipe:  # pylint: disable=too-many-instance-attributes
    """Recipe declaring how a set of package can be built."""

    # Path to the directory in which the recipe is defined
    path: str

    # Source modification timestamp
    timestamp: datetime

    # Set of source items to be downloaded
    sources: Set[Source]

    # Set of packages that are needed to build this recipe
    makedepends: Set[Dependency]

    # Full name and email address of this recipe’s maintainer
    maintainer: str

    # Docker image used to build this recipe
    image: str

    # Architecture that this recipe targets
    arch: str

    # Set of flags to be used by the build system
    flags: List[str]

    # Bash script for preparing (patching, moving) source files before build
    prepare: str

    # Bash script for building from source
    build: str

    # Set of packages to generate from the build artifacts
    packages: Dict[str, "Package"]


@dataclass
class Package:  # pylint: disable=too-many-instance-attributes
    """Installable package containing build artifacts."""

    # Name of this package, unique among all recipes of a repository
    name: str

    # Recipe used to generate this package
    parent: Recipe

    # Version number
    version: Version

    # Short description
    desc: str

    # URL to the homepage where more information can be found on this package
    url: str

    # Name of the section to which this package belongs
    section: str

    # Identifier for this package’s license
    license: str

    # Set of packages that must be installed for this package to work
    installdepends: Set[Dependency]

    # Set of packages that this package recommends installing
    recommends: Set[Dependency]

    # Set of packages that provide additional features for this package
    optdepends: Set[Dependency]

    # Set of incompatible packages
    conflicts: Set[Dependency]

    # Set of packages replaced by this package
    replaces: Set[Dependency]

    # Set of packages that this package provides
    provides: Set[Dependency]

    # Bash script for packaging build artifacts
    package: str

    # Bash script executed before this package is unpacked
    preinstall: str

    # Bash script executed after this package is unpacked
    configure: str

    # Bash script executed before this package is replaced with a newer version
    preupgrade: str

    # Bash script executed after this package is replaced with a newer version
    postupgrade: str

    # Bash script executed before this package is removed
    preremove: str

    # Bash script executed after this package is removed
    postremove: str

    def pkgid(self) -> str:
        """Get the unique identifier of this package."""
        return "_".join(
            (self.name, str(self.version).replace(":", "_"), self.parent.arch)
        )

    def filename(self) -> str:
        """Get the name of the archive corresponding to this package."""
        return os.path.join(self.parent.arch, self.pkgid() + ".ipk")

    def control_fields(self) -> str:
        """Get the control fields for this package."""
        control = textwrap.dedent(
            f"""\
            Package: {self.name}
            Description: {self.desc}
            Homepage: {self.url}
            Version: {self.version}
            Section: {self.section}
            Maintainer: {self.parent.maintainer}
            License: {self.license}
            Architecture: {self.parent.arch}
            """
        )

        for debian_name, field in (
            ("Depends", self.installdepends),
            ("Recommends", self.recommends),
            ("Suggests", self.optdepends),
            ("Conflicts", self.conflicts),
            ("Replaces", self.replaces),
            ("Provides", self.provides),
        ):
            if field:
                control += (
                    debian_name
                    + ": "
                    + ", ".join(sorted(dep.to_debian() for dep in field if dep))
                    + "\n"
                )

        return control
