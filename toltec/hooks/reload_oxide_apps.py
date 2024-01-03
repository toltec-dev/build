"""
Build hook for automatically reloading applications in oxide

After the artifacts are packaged, this hook looks for files in either
/opt/etc/draft or /opt/usr/share/applications and adds reload-oxide-apps to
configure, postupgrade, and postremove
"""
import os
import logging

from toltec.builder import Builder
from toltec.recipe import Package
from toltec.util import listener

logger = logging.getLogger(__name__)

OXIDE_HOOK = "\nreload-oxide-apps\n"


def register(builder: Builder) -> None:
    """Register the hook"""

    @listener(builder.post_package)
    def post_package(
        builder: Builder,  # pylint: disable=unused-argument
        package: Package,
        src_dir: str,  # pylint: disable=unused-argument
        pkg_dir: str,
    ) -> None:
        if os.path.exists(
            os.path.join(pkg_dir, "opt/usr/share/applications")
        ) or os.path.exists(os.path.join(pkg_dir, "opt/etc/draft")):
            package.configure += OXIDE_HOOK
            package.postupgrade += OXIDE_HOOK
            package.postremove += OXIDE_HOOK
