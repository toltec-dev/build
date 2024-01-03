"""
Build hook for patching all binary objects that access /dev/fb0 to depend on
librm2fb_client.so.1 after building a recipe.

After the build() script is run, and before the artifacts are packaged, this
hook looks for ARM ELF-files in the build directory that access /dev/fb0.
It then uses patchelf to add a dependency on librm2fb_client.so.1 to the
binaries. This behavior is only enabled if the recipe declares the
'patch_rm2fb' flag.
"""
import os
import logging
import shlex
from elftools.elf.elffile import ELFFile
from toltec.builder import Builder
from toltec.recipe import Recipe
from toltec.util import listener
from toltec.hooks.strip import walk_elfs, run_in_container, MOUNT_SRC

logger = logging.getLogger(__name__)


def register(builder: Builder) -> None:
    """Register the hook"""

    @listener(builder.post_build)
    def post_build(  # pylint: disable=too-many-locals
        builder: Builder, recipe: Recipe, src_dir: str
    ) -> None:
        if "patch_rm2fb" not in recipe.flags:
            return

        logger.debug("Adding dependency to rm2fb ('patch_rm2fb' flag is set)")
        # Search for binary objects that can be stripped
        binaries = []

        def filter_elfs(info: ELFFile, file_path: str) -> None:
            symtab = info.get_section_by_name(".symtab")
            if symtab is None or info.get_machine_arch() != "ARM":
                return

            dynamic = info.get_section_by_name(".dynamic")
            rodata = info.get_section_by_name(".rodata")
            if dynamic and rodata and rodata.data().find(b"/dev/fb0") != -1:
                binaries.append(file_path)

        walk_elfs(src_dir, filter_elfs)

        if not binaries:
            logger.debug("Skipping, no arm binaries found")
            return

        # Save original mtimes to restore them afterwards
        # This will prevent any Makefile rules to be triggered again
        # in packaging scripts that use `make install`
        original_mtime = {}

        script = [
            "export DEBIAN_FRONTEND=noninteractive",
            "apt-get update -qq",
            "apt-get install -qq --no-install-recommends patchelf",
        ]

        def docker_file_path(file_path: str) -> str:
            return shlex.quote(
                os.path.join(MOUNT_SRC, os.path.relpath(file_path, src_dir))
            )

        for file_path in binaries:
            original_mtime[file_path] = os.stat(file_path).st_mtime_ns

        script.append(
            "patchelf --add-needed librm2fb_client.so.1 "
            + " ".join(docker_file_path(file_path) for file_path in binaries)
        )

        run_in_container(builder, src_dir, logger, script)

        # Restore original mtimes
        for file_path, mtime in original_mtime.items():
            os.utime(file_path, ns=(mtime, mtime))
