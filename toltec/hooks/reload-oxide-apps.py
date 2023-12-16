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

OXIDE_HOOK = """
if systemctl --quiet is-active tarnish.service 2> /dev/null; then
    echo -n "Reloading Oxide applications: "
    local ret
    if type update-desktop-database &> /dev/null; then
        update-desktop-database --quiet
        ret=$?
    else
        /opt/bin/rot apps call reload 2> /dev/null
        ret=$?
    fi
    if [ $ret -eq 0 ]; then
        echo "Done!"
    else
        echo "Failed!"
    fi
fi
"""


def register(builder: Builder) -> None:
    @listener(builder.post_package)
    def post_package(
        builder: Builder, package: Package, src_dir: str, pkg_dir: str
    ) -> None:
        if os.path.exists(
            os.path.join(pkg_dir, "opt/usr/share/applications")
        ) or os.path.exists(os.path.join(pkg_dir, "opt/etc/draft")):
            package.configure += OXIDE_HOOK
            package.postupgrade += OXIDE_HOOK
            package.postremove += OXIDE_HOOK
