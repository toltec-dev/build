# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""Build recipes and create packages."""

import shutil
from typing import List, Mapping, Optional, Type
from types import TracebackType
import re
import os
import logging
import textwrap
from importlib.util import find_spec, module_from_spec
import docker
import requests
from . import hooks
from . import bash, util, ipk
from .recipe import RecipeBundle, Recipe, Package
from .version import DependencyKind

logger = logging.getLogger(__name__)


class BuildError(Exception):
    """Raised when a build step fails."""


class Builder:  # pylint: disable=too-few-public-methods
    """Helper class for building recipes."""

    # Detect non-local paths
    URL_REGEX = re.compile(r"[a-z]+://")

    # Prefix for all Toltec Docker images
    IMAGE_PREFIX = "ghcr.io/toltec-dev/"

    def __init__(self, work_dir: str, dist_dir: str) -> None:
        """
        Create a builder helper.

        :param work_dir: directory where packages are built
        :param dist_dir: directory where built packages are stored
        """
        self.work_dir = work_dir
        self.dist_dir = dist_dir

        try:
            self.docker = docker.from_env()
        except docker.errors.DockerException as err:
            raise BuildError(
                "Unable to connect to the Docker daemon. \
Please check that the service is running and that you have the necessary \
permissions."
            ) from err

        for hook in hooks.__all__:
            spec = find_spec(f"toltec.hooks.{hook}")
            if spec:
                module = module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore
                module.register(self)  # type: ignore
            else:
                raise RuntimeError(
                    f"Hook module 'toltec.hooks.{hook}' couldn’t be loaded"
                )

    def __enter__(self) -> "Builder":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.docker.close()

    @util.hook
    def post_parse(self, recipe: Recipe) -> None:
        """
        Triggered after a recipe has been parsed, before executing it.

        :param recipe: recipe object, may be modified by hook listeners
        """

    @util.hook
    def post_fetch_sources(self, recipe: Recipe, src_dir: str) -> None:
        """
        Triggered after the sources of a recipe have been fetched, before
        running the prepare() script.

        :param recipe: recipe object
        :param src_dir: folder in which sources have been extracted
        """

    @util.hook
    def post_prepare(self, recipe: Recipe, src_dir: str) -> None:
        """
        Triggered after the prepare() script of a recipe has been run.

        :param recipe: recipe object
        :param src_dir: folder in which sources have been prepared
        """

    @util.hook
    def post_build(self, recipe: Recipe, src_dir: str) -> None:
        """
        Triggered after a recipe’s artifacts have been built.

        :param recipe: recipe object
        :param src_dir: folder in which artifacts have been built
        """

    @util.hook
    def post_package(
        self, package: Package, src_dir: str, pkg_dir: str
    ) -> None:
        """
        Triggered after part of the artifacts from a build have been copied
        in place to the packaging directory.

        :param package: package object
        :param src_dir: folder in which artifacts have been built
        :param pkg_dir: folder in which artifacts to package have been copied
        """

    @util.hook
    def post_archive(self, package: Package, ar_path: str) -> None:
        """
        Triggered after a package archive has been generated.

        :param package: package object
        :param archive: path to the final package archive
        """

    def make(
        self,
        recipe_bundle: RecipeBundle,
        build_matrix: Optional[Mapping[str, Optional[List[Package]]]] = None,
        check_directory: bool = True,
    ) -> bool:
        """
        Build packages defined by a recipe.

        :param recipe_bundle: architecture versions of the recipe to make
        :param build_matrix: set of packages to build for each architecture
            (default: all supported packages for each architecture)
        :returns: true if all the requested packages were built correctly
        """
        if check_directory and not util.check_directory(
            self.work_dir,
            f"The build directory '{self.work_dir}' \
already exists.\nWould you like to [c]ancel, [r]emove that directory, \
or [k]eep it (not recommended)?",
        ):
            return False

        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(self.dist_dir, exist_ok=True)

        for name in (
            list(build_matrix.keys())
            if build_matrix is not None
            else list(recipe_bundle.keys())
        ):
            if not self._make_arch(
                recipe_bundle[name],
                os.path.join(self.work_dir, name),
                build_matrix[name] if build_matrix is not None else None,
            ):
                return False

        return True

    def _make_arch(
        self,
        recipe: Recipe,
        build_dir: str,
        packages: Optional[List[Package]] = None,
    ) -> bool:
        self.post_parse(recipe)

        src_dir = os.path.join(build_dir, "src")
        os.makedirs(src_dir, exist_ok=True)

        self._fetch_sources(recipe, src_dir)
        self.post_fetch_sources(recipe, src_dir)

        self._prepare(recipe, src_dir)
        self.post_prepare(recipe, src_dir)

        self._build(recipe, src_dir)
        self.post_build(recipe, src_dir)

        base_pkg_dir = os.path.join(build_dir, "pkg")
        os.makedirs(base_pkg_dir, exist_ok=True)

        for package in (
            packages if packages is not None else recipe.packages.values()
        ):
            pkg_dir = os.path.join(base_pkg_dir, package.name)
            os.makedirs(pkg_dir, exist_ok=True)

            self._package(package, src_dir, pkg_dir)
            self.post_package(package, src_dir, pkg_dir)

            ar_path = os.path.join(self.dist_dir, package.filename())
            ar_dir = os.path.dirname(ar_path)
            os.makedirs(ar_dir, exist_ok=True)

            self._archive(package, pkg_dir, ar_path)
            self.post_archive(package, ar_path)

        return True

    def _fetch_sources(
        self,
        recipe: Recipe,
        src_dir: str,
    ) -> None:
        """Fetch and extract all source files required to build a recipe."""
        logger.info("Fetching source files")

        for source in recipe.sources:
            filename = os.path.basename(source.url)
            local_path = os.path.join(src_dir, filename)

            if self.URL_REGEX.match(source.url) is None:
                # Get source file from the recipe’s directory
                shutil.copy2(os.path.join(recipe.path, source.url), local_path)
            else:
                # Fetch source file from the network
                req = requests.get(source.url, timeout=(3.05, 300))

                if req.status_code != 200:
                    raise BuildError(
                        f"Unexpected status code while fetching \
source file '{source.url}', got {req.status_code}"
                    )

                with open(local_path, "wb") as local:
                    for chunk in req.iter_content(chunk_size=1024):
                        local.write(chunk)

            # Verify checksum
            file_sha = util.file_sha256(local_path)
            if source.checksum not in ("SKIP", file_sha):
                raise BuildError(
                    f"Invalid checksum for source file {source.url}:\n"
                    f"  expected {source.checksum}\n"
                    f"  actual   {file_sha}"
                )

            # Automatically extract source archives
            if not source.noextract:
                if not util.auto_extract(local_path, src_dir):
                    logger.debug(
                        "Not extracting %s (unsupported archive type)",
                        local_path,
                    )

    @staticmethod
    def _prepare(recipe: Recipe, src_dir: str) -> None:
        """Prepare source files before building."""
        if not recipe.prepare:
            logger.debug("Skipping prepare (nothing to do)")
            return

        logger.info("Preparing source files")
        logs = bash.run_script(
            script=recipe.prepare,
            variables={
                "srcdir": src_dir,
            },
        )
        bash.pipe_logs(logger, logs, "prepare()")

    def _build(self, recipe: Recipe, src_dir: str) -> None:
        """Build artifacts for a recipe."""
        if not recipe.build:
            logger.debug("Skipping build (nothing to do)")
            return

        logger.info("Building artifacts")

        # Set fixed atime and mtime for all the source files
        epoch = int(recipe.timestamp.timestamp())

        for filename in util.list_tree(src_dir):
            os.utime(filename, (epoch, epoch))

        mount_src = "/src"
        repo_src = "/repo"
        uid = os.getuid()
        pre_script: List[str] = []

        # Install required dependencies
        build_deps = []
        host_deps = []

        for dep in recipe.makedepends:
            if dep.kind == DependencyKind.BUILD:
                build_deps.append(dep.package)
            elif dep.kind == DependencyKind.HOST:
                host_deps.append(dep.package)

        if build_deps:
            pre_script.extend(
                (
                    "export DEBIAN_FRONTEND=noninteractive",
                    "apt-get update -qq",
                    "apt-get install -qq --no-install-recommends"
                    ' -o Dpkg::Options::="--force-confdef"'
                    ' -o Dpkg::Options::="--force-confold"'
                    " -- " + " ".join(build_deps),
                )
            )

        if host_deps:
            opkg_conf_path = "$SYSROOT/etc/opkg/opkg.conf"
            pre_script.extend(
                (
                    'echo -n "dest root /',
                    "arch all 100",
                    "arch armv7-3.2 160",
                    "src/gz entware https://bin.entware.net/armv7sf-k3.2",
                    "arch rmall 200",
                    "src/gz toltec-rmall file:///repo/rmall",
                    f'" > "{opkg_conf_path}"',
                )
            )

            if recipe.arch != "rmall":
                pre_script.extend(
                    (
                        f'echo -n "arch {recipe.arch} 250',
                        f"src/gz toltec-{recipe.arch} file:///repo/{recipe.arch}",
                        f'" >> "{opkg_conf_path}"',
                    )
                )

            pre_script.extend(
                (
                    "opkg update --verbosity=0",
                    "opkg install --verbosity=0 --no-install-recommends"
                    " -- " + " ".join(host_deps),
                )
            )

        logs = bash.run_script_in_container(
            self.docker,
            image=self.IMAGE_PREFIX + recipe.image,
            mounts=[
                docker.types.Mount(
                    type="bind",
                    source=os.path.abspath(src_dir),
                    target=mount_src,
                ),
                docker.types.Mount(
                    type="bind",
                    source=os.path.abspath(self.dist_dir),
                    target=repo_src,
                ),
            ],
            variables={
                "srcdir": mount_src,
            },
            script="\n".join(
                (
                    *pre_script,
                    f'cd "{mount_src}"',
                    recipe.build,
                    f'chown -R {uid}:{uid} "{mount_src}"',
                )
            ),
        )
        bash.pipe_logs(logger, logs, "build()")

    @staticmethod
    def _package(package: Package, src_dir: str, pkg_dir: str) -> None:
        """Make a package from a recipe’s build artifacts."""
        logger.info("Packaging build artifacts for %s", package.name)
        logs = bash.run_script(
            script=package.package,
            variables={
                "srcdir": src_dir,
                "pkgdir": pkg_dir,
            },
        )

        bash.pipe_logs(logger, logs, "package()")
        logger.debug("Resulting tree:")

        for filename in util.list_tree(pkg_dir):
            logger.debug(
                " - %s",
                os.path.normpath(
                    os.path.join("/", os.path.relpath(filename, pkg_dir))
                ),
            )

    @staticmethod
    def _archive(package: Package, pkg_dir: str, ar_path: str) -> None:
        """Create an archive for a package."""
        logger.info("Creating archive %s", package.filename())

        # Convert install scripts to Debian format
        scripts = {}
        script_header = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail
            """
        )

        for name, script, action in (
            ("preinstall", "preinst", "install"),
            ("configure", "postinst", "configure"),
        ):
            function = getattr(package, name)

            if function:
                scripts[script] = "\n".join(
                    (
                        script_header,
                        textwrap.dedent(
                            f"""\
                            if [[ $1 = {action} ]]; then
                                script() {{
                            """
                        ),
                        function,
                        textwrap.dedent(
                            """\
                                }
                                script
                            fi
                            """
                        ),
                    )
                )

        for step in ("pre", "post"):
            if getattr(package, step + "upgrade") or getattr(
                package, step + "remove"
            ):
                script = script_header

                for action in ("upgrade", "remove"):
                    function = getattr(package, step + action)

                    if function:
                        script += "\n".join(
                            (
                                textwrap.dedent(
                                    f"""\
                                    if [[ $1 = {action} ]]; then
                                        script() {{
                                    """
                                ),
                                function,
                                textwrap.dedent(
                                    """\
                                        }
                                        script
                                    fi
                                    """
                                ),
                            )
                        )

                scripts[step + "rm"] = script

        logger.debug("Install scripts:")

        if scripts:
            for script in sorted(scripts):
                logger.debug(" - %s", script)
        else:
            logger.debug("(none)")

        epoch = int(package.parent.timestamp.timestamp())

        with open(ar_path, "wb") as file:
            ipk.write(
                file,
                epoch=epoch,
                pkg_dir=pkg_dir,
                metadata=package.control_fields(),
                scripts=scripts,
            )

        # Set fixed atime and mtime for the resulting archive
        os.utime(ar_path, (epoch, epoch))
