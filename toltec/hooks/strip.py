"""
Build hook for stripping all binary objects after building a recipe.

After the build() script is run, and before the artifacts are packaged, this
hook looks for ELF-files in the build directory and strips them. This
behavior is disabled if the recipe declares the 'nostrip' flag.
"""
import os
import logging
import shlex
from typing import Callable, List
import docker
from elftools.elf.elffile import ELFFile, ELFError
from toltec import bash
from toltec.builder import Builder
from toltec.recipe import Recipe
from toltec.util import listener

logger = logging.getLogger(__name__)

MOUNT_SRC = "/src"
TOOLCHAIN = "toolchain:v1.3.1"


def walk_elfs(src_dir: str, for_each: Callable) -> None:
    """Walk through all the ELF binaries in a directory and run a method for each of them"""
    for directory, _, files in os.walk(src_dir):
        for file_name in files:
            file_path = os.path.join(directory, file_name)

            try:
                with open(file_path, "rb") as file:
                    for_each(ELFFile(file), file_path)
            except ELFError:
                # Ignore non-ELF files
                pass
            except IsADirectoryError:
                # Ignore directories
                pass


def run_in_container(
    builder: Builder, src_dir: str, _logger: logging.Logger, script: List[str]
) -> None:
    """Run a script in a container and log output"""
    logs = bash.run_script_in_container(
        builder.docker,
        image=builder.IMAGE_PREFIX + TOOLCHAIN,
        mounts=[
            docker.types.Mount(
                type="bind",
                source=os.path.abspath(src_dir),
                target=MOUNT_SRC,
            )
        ],
        variables={},
        script="\n".join(script),
    )
    bash.pipe_logs(_logger, logs)


def register(builder: Builder) -> None:
    """Register the hook"""

    @listener(builder.post_build)
    def post_build(  # pylint: disable=too-many-locals,too-many-branches
        builder: Builder, recipe: Recipe, src_dir: str
    ) -> None:
        if "nostrip" in recipe.flags:
            logger.debug("Skipping strip ('nostrip' flag is set)")
            return

        # Search for binary objects that can be stripped
        strip_arm: List[str] = []
        strip_x86: List[str] = []

        def filter_elfs(info: ELFFile, file_path: str) -> None:
            symtab = info.get_section_by_name(".symtab")
            if not symtab:
                return
            if info.get_machine_arch() == "ARM":
                strip_arm.append(file_path)
            elif info.get_machine_arch() in ("x86", "x64"):
                strip_x86.append(file_path)

        walk_elfs(src_dir, filter_elfs)

        if not strip_arm and not strip_x86:
            logger.debug("Skipping, no binaries found")
            return

        # Save original mtimes to restore them afterwards
        # This will prevent any Makefile rules to be triggered again
        # in packaging scripts that use `make install`
        original_mtime = {}

        for file_path in strip_arm + strip_x86:
            original_mtime[file_path] = os.stat(file_path).st_mtime_ns

        # Run strip on found binaries
        script = []

        def docker_file_path(file_path: str) -> str:
            return shlex.quote(
                os.path.join(MOUNT_SRC, os.path.relpath(file_path, src_dir))
            )

        # Strip debugging symbols and unneeded sections
        if strip_x86:
            script.append(
                "strip --strip-all -- "
                + " ".join(
                    docker_file_path(file_path) for file_path in strip_x86
                )
            )

            logger.debug("x86 binaries to be stripped:")

            for file_path in strip_x86:
                logger.debug(
                    " - %s",
                    os.path.relpath(file_path, src_dir),
                )

        if strip_arm:
            script.append(
                '"${CROSS_COMPILE}strip" --strip-all -- '
                + " ".join(
                    docker_file_path(file_path) for file_path in strip_arm
                )
            )

            logger.debug("ARM binaries to be stripped:")

            for file_path in strip_arm:
                logger.debug(
                    " - %s",
                    os.path.relpath(file_path, src_dir),
                )

        run_in_container(builder, src_dir, logger, script)

        # Restore original mtimes
        for file_path, mtime in original_mtime.items():
            os.utime(file_path, ns=(mtime, mtime))
