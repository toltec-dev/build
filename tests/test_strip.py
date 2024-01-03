# Copyright (c) 2023 The Toltec Contributors
# SPDX-License-Identifier: MIT

import unittest
import subprocess
import shutil

from os import path
from tempfile import TemporaryDirectory
from toltec.hooks.strip import walk_elfs
from elftools.elf.elffile import ELFFile


class TestBuild(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = path.dirname(path.realpath(__file__))
        self.fixtures_dir = path.join(self.dir, "fixtures")

    def test_strip(self) -> None:
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
            walk_elfs(
                work_dir,
                lambda i, p: self.assertIsNone(
                    i.get_section_by_name(".symtab"), f"{p} is not stripped"
                ),
            )

        with TemporaryDirectory() as tmp_dir:
            src_dir = path.join(self.fixtures_dir, "hello")
            rec_dir = path.join(tmp_dir, "src")
            work_dir = path.join(tmp_dir, "build")
            dist_dir = path.join(tmp_dir, "dist")
            shutil.copytree(src_dir, rec_dir)
            replacements = {"flags=()": "flags=(nostrip)"}
            with open(
                path.join(src_dir, "package"), "rt", encoding="utf-8"
            ) as infile, open(
                path.join(rec_dir, "package"), "wt", encoding="utf-8"
            ) as outfile:
                for line in infile:
                    for src, target in replacements.items():
                        line = line.replace(src, target)
                    outfile.write(line)

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
            walk_elfs(
                work_dir,
                lambda i, p: self.assertIsNotNone(
                    i.get_section_by_name(".symtab"), f"{p} is stripped"
                ),
            )
