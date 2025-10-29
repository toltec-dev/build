# Copyright (c) 2023 The Toltec Contributors
# SPDX-License-Identifier: MIT

import unittest
import subprocess

from os import path
from tempfile import TemporaryDirectory
from elftools.elf.elffile import ELFFile


class TestBuild(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = path.dirname(path.realpath(__file__))
        self.fixtures_dir = path.join(self.dir, "fixtures")

    def test_arch(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            rec_dir = path.join(self.fixtures_dir, "hello")
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
            with open(
                path.join(tmp_dir, "build", "rm1", "src", "hello"), "rb"
            ) as f:
                self.assertEqual(ELFFile(f).get_machine_arch(), "ARM")
            with open(
                path.join(tmp_dir, "build", "rmpp", "src", "hello"), "rb"
            ) as f:
                self.assertEqual(ELFFile(f).get_machine_arch(), "AArch64")
