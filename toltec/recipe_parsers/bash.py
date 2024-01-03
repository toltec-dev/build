# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""Parse recipes from Bash files."""

import warnings
from itertools import product
from typing import Any, Dict, Generator, Iterable, Optional, Tuple
import os
import dateutil.parser
from ..version import (
    Version,
    InvalidVersionError,
    Dependency,
    InvalidDependencyError,
    DependencyKind,
)
from .. import bash
from ..recipe import (
    RecipeBundle,
    Recipe,
    Package,
    RecipeError,
    RecipeWarning,
    Source,
)


def parse(path: str) -> RecipeBundle:
    """
    Load a recipe defined as a Bash file.

    :param path: path to the directory containing the recipe definition
    :returns: loaded recipe
    """
    with open(os.path.join(path, "package"), "r", encoding="UTF-8") as recipe:
        result = {}
        definition = recipe.read()
        variables, functions = bash.get_declarations(definition)

        for arch, variables, functions in _instantiate_arch(
            path, variables, functions
        ):
            result[arch] = _parse_recipe(path, variables, functions)

        return result


def _instantiate_arch(
    path: str,
    variables: bash.Variables,
    functions: bash.Functions,
) -> Generator[Tuple[str, bash.Variables, bash.Functions], None, None]:
    """
    Instantiate a recipe definition for each supported architecture.

    :param path: path to the directory containing the recipe definition
    :param variables: Bash variables defined in the recipe
    :param functions: Bash functions defined in the recipe
    :returns: instantiated variables and functions
    """
    archs = _pop_field_indexed(path, variables, "archs", ["rmall"])
    assert archs is not None

    for arch in archs:
        loc_vars: bash.Variables = variables.copy()
        loc_funcs: bash.Functions = functions.copy()
        loc_vars["arch"] = arch

        # Merge variables suffixed with the selected architecture
        # into normal variables, drop other arch-specific declarations
        for name, value in list(loc_vars.items()):
            last_underscore = name.rfind("_")

            if last_underscore == -1:
                continue

            name_arch = name[last_underscore + 1 :]

            if name_arch not in archs:
                continue

            del loc_vars[name]

            if name_arch != arch:
                continue

            name = name[:last_underscore]

            if name not in loc_vars:
                loc_vars[name] = value
            else:
                normal_value = loc_vars[name]

                if isinstance(normal_value, str):
                    if not isinstance(value, str):
                        raise RecipeError(
                            path,
                            f"Field '{name}' was declared several times with \
different types",
                        )

                    loc_vars[name] = value

                if isinstance(normal_value, list):
                    if not isinstance(value, list):
                        raise RecipeError(
                            path,
                            f"Field '{name}' was declared several times with \
different types",
                        )

                    normal_value.extend(value)

        yield arch or "", loc_vars, loc_funcs


def _parse_recipe(  # pylint: disable=too-many-locals, disable=too-many-statements
    path: str,
    variables: bash.Variables,
    functions: bash.Functions,
) -> Recipe:
    """
    Load an architecture-specialized recipe.

    :param path: path to the directory containing the recipe definition
    :param variables: specialized Bash variables for the recipe
    :param functions: specialized Bash functions for the recipe
    :raises RecipeError: if the recipe contains an error
    :returns: loaded recipe
    """
    attrs: Dict[str, Any] = {}
    attrs["path"] = path
    raw_vars: bash.Variables = {}

    flags = raw_vars["flags"] = _pop_field_indexed(path, variables, "flags", [])
    attrs["flags"] = [flag or "" for flag in flags]

    timestamp_str = _pop_field_string(path, variables, "timestamp")
    raw_vars["timestamp"] = timestamp_str

    try:
        attrs["timestamp"] = dateutil.parser.isoparse(timestamp_str)
    except ValueError as err:
        raise RecipeError(
            path, "Field 'timestamp' does not contain a valid ISO-8601 date"
        ) from err

    sources = _pop_field_indexed(path, variables, "source", [])
    raw_vars["source"] = sources

    sha256sums = _pop_field_indexed(path, variables, "sha256sums", [])
    raw_vars["sha256sums"] = sha256sums

    noextract = _pop_field_indexed(path, variables, "noextract", [])
    raw_vars["noextract"] = noextract

    if len(sources) != len(sha256sums):
        raise RecipeError(
            path,
            f"Expected the same number of sources and checksums, got \
{len(sources)} source(s) and {len(sha256sums)} checksum(s)",
        )

    attrs["sources"] = set()

    for source, checksum in zip(sources, sha256sums):
        attrs["sources"].add(
            Source(
                url=source or "",
                checksum=checksum or "SKIP",
                noextract=os.path.basename(source or "") in noextract,
            )
        )

    makedepends_raw = _pop_field_indexed(path, variables, "makedepends", [])
    raw_vars["makedepends"] = makedepends_raw
    attrs["makedepends"] = {
        Dependency.parse(dep or "") for dep in makedepends_raw
    }

    attrs["maintainer"] = raw_vars["maintainer"] = _pop_field_string(
        path, variables, "maintainer"
    )

    attrs["image"] = raw_vars["image"] = _pop_field_string(
        path, variables, "image", ""
    )

    attrs["arch"] = raw_vars["arch"] = _pop_field_string(
        path, variables, "arch"
    )

    if attrs["image"] and "build" not in functions:
        raise RecipeError(
            path,
            "Missing build() function for a recipe which declares a \
build image",
        )

    if not attrs["image"] and "build" in functions:
        raise RecipeError(
            path,
            "Missing image declaration for a recipe which has a \
build() step",
        )

    attrs["prepare"] = functions.pop("prepare", "")
    attrs["build"] = functions.pop("build", "")

    pkgnames = _pop_field_indexed(path, variables, "pkgnames")
    attrs["packages"] = {}

    result = Recipe(**attrs)

    if len(pkgnames) == 1:
        # Single-package recipe: use global declarations
        pkg_name = pkgnames[0]
        assert pkg_name is not None
        variables["pkgname"] = pkg_name
        attrs["packages"][pkg_name] = _parse_package(
            result,
            variables.copy(),
            raw_vars.copy(),
            functions,
        )
    else:
        # Split-package recipe: load package-local declarations
        pkg_decls = {}

        for sub_pkg_name in pkgnames:
            assert sub_pkg_name is not None

            if sub_pkg_name not in functions:
                raise RecipeError(
                    path,
                    f"Missing required function {sub_pkg_name}() for \
corresponding package",
                )

            pkg_def = functions.pop(sub_pkg_name)
            context = bash.put_variables(
                {
                    **raw_vars,
                    **variables,
                    "pkgname": sub_pkg_name,
                }
            )
            pkg_decls[sub_pkg_name] = bash.get_declarations(context + pkg_def)

            for var_name in raw_vars:
                del pkg_decls[sub_pkg_name][0][var_name]

        for sub_pkg_name, (pkg_vars, pkg_funcs) in pkg_decls.items():
            attrs["packages"][sub_pkg_name] = _parse_package(
                result,
                pkg_vars,
                raw_vars.copy(),
                {**functions, **pkg_funcs},
            )

    _add_script_header(
        result,
        ("prepare", "build"),
        {**raw_vars, **variables},
        functions,
    )

    return result


def _parse_package(  # pylint: disable=too-many-locals, disable=too-many-statements
    parent: Recipe,
    variables: bash.Variables,
    raw_vars: bash.Variables,
    functions: bash.Functions,
) -> Package:
    """
    Load a package.

    :param parent: specialized recipe which declares this package
    :param variables: variables declared in the package
    :param raw_vars: variables used to populate fields in the parent recipe
    :param functions: functions declared in the package
    :raises RecipeError: if the package contains an error
    """
    attrs: Dict[str, Any] = {}
    attrs["parent"] = parent

    # Parse fields
    attrs["name"] = raw_vars["pkgname"] = _pop_field_string(
        parent.path, variables, "pkgname"
    )

    pkgver_str = _pop_field_string(parent.path, variables, "pkgver")
    raw_vars["pkgver"] = pkgver_str

    try:
        attrs["version"] = Version.parse(pkgver_str)
    except InvalidVersionError as err:
        raise RecipeError(
            parent.path, f"Failed to parse version number: '{pkgver_str}'"
        ) from err

    attrs["desc"] = raw_vars["pkgdesc"] = _pop_field_string(
        parent.path, variables, "pkgdesc"
    )

    attrs["url"] = raw_vars["url"] = _pop_field_string(
        parent.path, variables, "url"
    )

    attrs["section"] = raw_vars["section"] = _pop_field_string(
        parent.path, variables, "section"
    )

    attrs["license"] = raw_vars["license"] = _pop_field_string(
        parent.path, variables, "license"
    )

    for field in (
        "installdepends",
        "recommends",
        "optdepends",
        "conflicts",
        "replaces",
        "provides",
    ):
        field_raw = _pop_field_indexed(parent.path, variables, field, [])
        raw_vars[field] = field_raw
        attrs[field] = set()

        for dep_raw in field_raw:
            assert dep_raw is not None
            try:
                dep = Dependency.parse(dep_raw)
            except (InvalidVersionError, InvalidDependencyError) as err:
                raise RecipeError(
                    parent.path, f"Failed to parse dependency: '{dep_raw}'"
                ) from err

            if dep.kind != DependencyKind.HOST:
                raise RecipeError(
                    parent.path,
                    f"Only host packages are supported in the \
'{field}' field, cannot add dependency '{dep}'",
                )

            attrs[field].add(dep)

    # Parse functions
    attrs["package"] = functions.pop("package")

    for action in ("preinstall", "configure"):
        attrs[action] = functions.pop(action, "")

    for rel, step in product(("pre", "post"), ("remove", "upgrade")):
        attrs[rel + step] = functions.pop(rel + step, "")

    # Check that remaining variables and functions are prefixed
    for var_name in variables.keys():
        if not var_name.startswith("_"):
            warnings.warn(
                f"{parent.path}: Unknown field '{var_name}'. Make sure to \
prefix the names of custom fields with '_'",
                RecipeWarning,
            )

    for func_name in functions.keys():
        if not func_name.startswith("_"):
            warnings.warn(
                f"{parent.path}: Unknown function '{func_name}'. Make sure to \
prefix the names of custom functions with '_'",
                RecipeWarning,
            )

    result = Package(**attrs)
    _add_script_header(
        result,
        (
            "package",
            "preinstall",
            "configure",
            "preremove",
            "postremove",
            "preupgrade",
            "postupgrade",
        ),
        {**raw_vars, **variables},
        functions,
    )
    return result


def _pop_field_string(
    path: str,
    variables: bash.Variables,
    name: str,
    default: Optional[str] = None,
) -> str:
    if name not in variables:
        if default is None:
            raise RecipeError(path, f"Missing required field '{name}'")
        return default

    value = variables.pop(name)

    if not isinstance(value, str):
        raise RecipeError(
            path,
            f"Field '{name}' must be a string, got a {type(value).__name__}",
        )

    return value


def _pop_field_indexed(
    path: str,
    variables: bash.Variables,
    name: str,
    default: Optional[bash.IndexedArray] = None,
) -> bash.IndexedArray:
    if name not in variables:
        if default is None:
            raise RecipeError(path, f"Missing required field '{name}'")
        return default

    value = variables.pop(name)

    if not isinstance(value, list):
        _name = type(value).__name__
        raise RecipeError(
            path,
            f"Field '{name}' must be an indexed array, got a {_name}",
        )

    return value


def _add_script_header(
    obj: object,
    keys: Iterable[str],
    variables: bash.Variables,
    functions: bash.Functions,
) -> None:
    header = "\n".join(
        (
            bash.put_variables(variables),
            bash.put_functions(functions),
        )
    )

    for key in keys:
        if getattr(obj, key):
            setattr(obj, key, header + getattr(obj, key))
