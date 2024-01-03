"""
Build hook to automatically add install-lib helper functions

After the artifacts are packaged, this hook will look for known install-lib
methods and add them to scripts if found.
"""
import logging

from typing import Set, Iterable
from toltec.builder import Builder
from toltec.recipe import Package
from toltec.util import listener

logger = logging.getLogger(__name__)

METHODS = {}


def add_method(name: str, src: str, *depends: Iterable[str]) -> None:
    """Add a method to be automatically added to scripts that use it"""
    METHODS[name] = (
        src,
        depends,
    )


def register(builder: Builder) -> None:
    """Register the hook"""

    @listener(builder.post_package)
    def post_package(
        builder: Builder,  # pylint: disable=unused-argument
        package: Package,
        src_dir: str,  # pylint: disable=unused-argument
        pkg_dir: str,  # pylint: disable=unused-argument
    ) -> None:
        for name in (
            "configure",
            "postremove",
            "postupgrade",
            "preinstall",
            "preremove",
            "preupgrade",
        ):
            function = getattr(package, name)
            methods: Set[str] = set()
            for method in METHODS:  # pylint: disable=consider-using-dict-items
                if method in function:
                    methods.add(method)
                    src, depends = METHODS[method]
                    methods.update(depends)  # type: ignore

            for method in methods:
                src, depends = METHODS[method]
                function = f"""
{method}() {{
    {src}
}}
{function}
"""

            setattr(package, name, function)

    add_method("is-enabled", 'systemctl --quiet is-enabled "$1" 2> /dev/null')
    add_method(
        "is-masked",
        '[[ "$(systemctl is-enabled "$1" 2> /dev/null)" == "masked" ]]',
    )
    add_method("is-active", 'systemctl --quiet is-active "$1" 2> /dev/null')
    add_method(
        "get-conflicts",
        """
    # Find enabled units that have a conflicting name
    for name in $(systemctl cat "$1" | awk -F'=' '/^Alias=/{print $2}'); do
        local realname
        if realname="$(basename "$(readlink "/etc/systemd/system/$name")")"; then
            echo "$realname"
        fi
    done

    # Find units that are declared as conflicting
    # (systemd automatically adds a conflict with "shutdown.target" to all
    # service units see systemd.service(5), section "Automatic Dependencies")
    systemctl show "$1" | awk -F'=' '/^Conflicts=/{print $2}' \
        | sed 's|\bshutdown.target\b||'
    """,
    )
    add_method(
        "how-to-enable",
        """
    for conflict in $(get-conflicts "$1"); do
        if is-enabled "$conflict"; then
            echo "$ systemctl disable --now ${conflict/.service/}"
        fi
    done

    echo "$ systemctl enable --now ${1/.service/}"
    """,
        "is-enabled",
        "get-conflicts",
    )
    add_method(
        "reload-oxide-apps",
        """
    if ! is-active tarnish.service; then
        return
    fi
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
    """,
        "is-active",
    )
    add_method(
        "add-bind-mount",
        """
    local unit_name
    local unit_path
    unit_name="$(systemd-escape --path "$2").mount"
    unit_path="/lib/systemd/system/$unit_name"

    if [[ -e $unit_path ]]; then
        echo "Bind mount configuration for '$2' already exists, updating"
    else
        echo "Mounting '$1' over '$2'"
    fi

    cat > "$unit_path" << UNIT
    [Unit]
    Description=Bind mount $1 over $2
    DefaultDependencies=no
    Conflicts=umount.target
    Before=local-fs.target umount.target

    [Mount]
    What=$1
    Where=$2
    Type=none
    Options=bind

    [Install]
    WantedBy=local-fs.target
    UNIT

    systemctl daemon-reload
    systemctl enable "$unit_name"
    systemctl restart "$unit_name"
    """,
    )
    add_method(
        "remove-bind-mount",
        """
    local unit_name
    local unit_path
    unit_name="$(systemd-escape --path "$1").mount"
    unit_path="/lib/systemd/system/$unit_name"

    if [[ ! -e $unit_path ]]; then
        echo "No existing bind mount for '$1'"
        return 1
    fi

    echo "Removing mount over '$1'"
    systemctl disable "$unit_name"
    systemctl stop "$unit_name"
    rm "$unit_path"
    systemctl daemon-reload
    """,
    )
    add_method(
        "unit-exists",
        '[ "$(systemctl --quiet list-unit-files "${1}" | grep -c "${1}")" -eq 1 ]',
    )
    add_method(
        "disable-unit",
        """
    if ! unit-exists "${1}"; then
        return
    fi
    if is-active "$1"; then
        echo "Stopping ${1}"
        systemctl stop "${1}"
    fi
    if is-enabled "${1}"; then
        echo "Disabling ${1}"
        systemctl disable "${1}"
    fi
    """,
        "unit-exists",
        "is-active",
        "is-enabled",
    )
