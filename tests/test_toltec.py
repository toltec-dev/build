# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT

from os import path
import unittest
from tempfile import TemporaryDirectory
import subprocess


def filter_index_entry(index_entry):
    return "\n".join(
        item
        for item in index_entry.split("\n")
        if not (item.startswith("SHA256sum:") or item.startswith("Size:"))
    )


class TestBuild(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = path.dirname(path.realpath(__file__))
        self.fixtures_dir = path.join(self.dir, "fixtures")

    def test_build_rmkit(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            rec_dir = path.join(self.fixtures_dir, "rmkit")
            work_dir = path.join(tmp_dir, "build")
            dist_dir = path.join(tmp_dir, "dist")

            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "toltec",
                    "--work-dir",
                    work_dir,
                    "--dist-dir",
                    dist_dir,
                    "--",
                    rec_dir,
                ],
                capture_output=True,
                check=False,
            )
            self.assertEqual(
                result.returncode, 0, result.stderr.decode("utf-8")
            )
            self.assertEqual(result.stdout.decode("utf-8"), "")
            self.assertEqual(
                result.stderr.decode("utf-8"),
                """\
[    INFO] toltec.builder: Fetching source files
[    INFO] toltec.builder: Preparing source files
[    INFO] toltec.builder: Building artifacts
[    INFO] toltec.builder: Packaging build artifacts for bufshot
[    INFO] toltec.builder: Creating archive rmall/bufshot_0.1.0-5_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for genie
[    INFO] toltec.builder: Creating archive rmall/genie_0.1.5-3_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for harmony
[    INFO] toltec.builder: Creating archive rmall/harmony_0.1.3-3_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for iago
[    INFO] toltec.builder: Creating archive rmall/iago_0.1.0-4_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for lamp
[    INFO] toltec.builder: Creating archive rmall/lamp_0.1.0-4_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for mines
[    INFO] toltec.builder: Creating archive rmall/mines_0.1.2-4_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for nao
[    INFO] toltec.builder: Creating archive rmall/nao_0.1.2-3_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for remux
[    INFO] toltec.builder: Creating archive rmall/remux_0.1.9-4_rmall.ipk
[    INFO] toltec.builder: Packaging build artifacts for simple
[    INFO] toltec.builder: Creating archive rmall/simple_0.1.4-3_rmall.ipk
[    INFO] toltec.repo: Generating package index
""",
            )

            with open(path.join(dist_dir, "rmall", "Packages"), "r") as index:
                index_data = index.read()
                index_entries = set(
                    filter_index_entry(entry)
                    for entry in index_data.split("\n\n")
                    if entry
                )

                self.assertEqual(
                    index_entries,
                    {
                        """Package: simple
Description: Simple app script for writing scripted applications
Homepage: https://rmkit.dev/apps/sas
Version: 0.1.4-3
Section: devel
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display
Filename: simple_0.1.4-3_rmall.ipk""",
                        """Package: remux
Description: Launcher that supports multi-tasking applications
Homepage: https://rmkit.dev/apps/remux
Version: 0.1.9-4
Section: launchers
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display
Filename: remux_0.1.9-4_rmall.ipk""",
                        """Package: nao
Description: Nao Package Manager: opkg UI built with SAS
Homepage: https://rmkit.dev/apps/nao
Version: 0.1.2-3
Section: admin
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display, simple
Filename: nao_0.1.2-3_rmall.ipk""",
                        """Package: mines
Description: Mine detection game
Homepage: https://rmkit.dev/apps/minesweeper
Version: 0.1.2-4
Section: games
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display
Filename: mines_0.1.2-4_rmall.ipk""",
                        """Package: lamp
Description: config based stroke injection utility
Homepage: https://rmkit.dev/apps/lamp
Version: 0.1.0-4
Section: utils
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display
Filename: lamp_0.1.0-4_rmall.ipk""",
                        """Package: iago
Description: overlay for drawing shapes via stroke injection
Homepage: https://rmkit.dev/apps/iago
Version: 0.1.0-4
Section: utils
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display, lamp
Filename: iago_0.1.0-4_rmall.ipk""",
                        """Package: harmony
Description: Procedural sketching app
Homepage: https://rmkit.dev/apps/harmony
Version: 0.1.3-3
Section: drawing
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display
Filename: harmony_0.1.3-3_rmall.ipk""",
                        """Package: genie
Description: Gesture engine that connects commands to gestures
Homepage: https://rmkit.dev/apps/genie
Version: 0.1.5-3
Section: utils
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display
Filename: genie_0.1.5-3_rmall.ipk""",
                        """Package: bufshot
Description: program for saving the framebuffer as a png
Homepage: https://github.com/rmkit-dev/rmkit/tree/master/src/bufshot
Version: 0.1.0-5
Section: utils
Maintainer: raisjn <of.raisjn@gmail.com>
License: MIT
Architecture: rmall
Depends: display
Filename: bufshot_0.1.0-5_rmall.ipk""",
                    },
                )
