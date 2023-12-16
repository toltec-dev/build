"""
Build hook for patching all binary objects to depend on librm2fb_client.so.1
after building a recipe.

After the build() script is run, and before the artifacts are packaged, this
hook looks for ELF-files in the build directory and uses patchelf to add a
dependency on librm2fb_client.so.1 to them. This behavior is only enabled if the
recipe declares the 'patch_rm2fb' flag.
"""
import os
import logging
import docker
import shlex
from elftools.elf.elffile import ELFFile, ELFError
from toltec import bash
from toltec.builder import Builder
from toltec.recipe import Recipe
from toltec.util import listener

logger = logging.getLogger(__name__)

MOUNT_SRC = "/src"


def register(builder: Builder) -> None:
    @listener(builder.post_build)
    def post_build(builder: Builder, recipe: Recipe, src_dir: str) -> None:
        if "patch_rm2fb" not in recipe.flags:
            return

        logger.debug("Adding dependency to rm2fb ('patch_rm2fb' flag is set)")
        # Search for binary objects that can be stripped
        binaries = []

        for directory, _, files in os.walk(src_dir):
            for file_name in files:
                file_path = os.path.join(directory, file_name)

                try:
                    info = ELFFile.load_from_path(file_path)
                    symtab = info.get_section_by_name(".symtab")

                    if symtab:
                        if info.get_machine_arch() == "ARM":
                            binaries.append(file_path)
                except ELFError:
                    # Ignore non-ELF files
                    pass
                except IsADirectoryError:
                    # Ignore directories
                    pass

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
                + " ".join(
                    docker_file_path(file_path) for file_path in binaries
                )
            )

        logs = bash.run_script_in_container(
            builder.docker,
            image=builder.IMAGE_PREFIX + "toolchain:v2.1",
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
        bash.pipe_logs(logger, logs)

        # Restore original mtimes
        for file_path, mtime in original_mtime.items():
            os.utime(file_path, ns=(mtime, mtime))
