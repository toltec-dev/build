# Copyright (c) 2022 The Toltec Contributors
# SPDX-License-Identifier: MIT

import unittest
import tarfile
from tempfile import TemporaryDirectory
import os
from toltec import ipk
from io import BytesIO


test_package = {
    "epoch": 1337,
    "metadata": "Test: OK\n",
    "scripts": {"postinst": "echo OK"},
    "data": [
        {
            "type": "file",
            "path": "./file1",
            "contents": "file 1\ntest\n",
            "mode": 0o644,
        },
        {
            "type": "dir",
            "path": "./zsubfolder",
            "mode": 0o755,
        },
        {
            "type": "file",
            "path": "./zsubfolder/file2",
            "contents": "this is\nfile 2",
            "mode": 0o400,
        },
    ],
}


class TestIpk(unittest.TestCase):
    def setUp(self):
        # Create data tree
        self.temp_dir = TemporaryDirectory()
        temp = self.temp_dir.name

        for member in test_package["data"]:
            if member["type"] == "file":
                with open(temp + "/" + member["path"], "w") as file:
                    file.write(member["contents"])

                os.chmod(temp + "/" + member["path"], member["mode"])
            else:
                os.mkdir(temp + "/" + member["path"], member["mode"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_control(self):
        output = BytesIO()
        ipk.write_control(
            output,
            test_package["epoch"],
            test_package["metadata"],
            test_package["scripts"],
        )
        output.seek(0)

        with tarfile.TarFile.open(fileobj=output) as archive:
            members = archive.getmembers()
            self.assertEqual(len(members), 3)

            self.assertTrue(members[0].isdir())
            self.assertEqual(members[0].name, ".")
            self.assertEqual(members[0].size, 0)
            self.assertEqual(members[0].mode, 0o755)

            self.assertTrue(members[1].isfile())
            self.assertEqual(members[1].name, "./control")
            self.assertEqual(members[1].size, len(test_package["metadata"]))
            self.assertEqual(members[1].mode, 0o644)
            self.assertEqual(
                archive.extractfile(members[1]).read().decode(),
                test_package["metadata"],
            )

            self.assertTrue(members[2].isfile())
            self.assertEqual(members[2].name, "./postinst")
            self.assertEqual(
                members[2].size, len(test_package["scripts"]["postinst"])
            )
            self.assertEqual(members[2].mode, 0o755)
            self.assertEqual(
                archive.extractfile(members[2]).read().decode(),
                test_package["scripts"]["postinst"],
            )

            for member in members:
                self.assertEqual(member.uid, 0)
                self.assertEqual(member.gid, 0)
                self.assertEqual(member.uname, "")
                self.assertEqual(member.gname, "")
                self.assertEqual(member.mtime, test_package["epoch"])

    def test_write_data_empty(self):
        output = BytesIO()
        ipk.write_data(output, test_package["epoch"])
        output.seek(0)

        with tarfile.TarFile.open(fileobj=output) as archive:
            self.assertEqual(archive.getmembers(), [])

    def test_write_data_dir(self):
        output = BytesIO()
        ipk.write_data(output, test_package["epoch"], self.temp_dir.name)
        output.seek(0)

        with tarfile.TarFile.open(fileobj=output) as archive:
            members = archive.getmembers()
            self.assertEqual(len(members), 4)

            self.assertTrue(members[0].isdir())
            self.assertEqual(members[0].name, ".")
            self.assertEqual(members[0].size, 0)
            self.assertEqual(members[0].mode, 0o700)

            for expect, member in zip(test_package["data"], members[1:]):
                if expect["type"] == "file":
                    self.assertTrue(member.isfile())
                    self.assertEqual(member.name, expect["path"])
                    self.assertEqual(member.size, len(expect["contents"]))
                    self.assertEqual(member.mode, expect["mode"])
                    self.assertEqual(
                        archive.extractfile(member).read().decode(),
                        expect["contents"],
                    )
                else:
                    self.assertTrue(member.isdir())
                    self.assertEqual(member.name, expect["path"])
                    self.assertEqual(member.size, 0)
                    self.assertEqual(member.mode, expect["mode"])

                self.assertEqual(member.uid, 0)
                self.assertEqual(member.gid, 0)
                self.assertEqual(member.uname, "")
                self.assertEqual(member.gname, "")
                self.assertEqual(member.mtime, test_package["epoch"])

    def test_write_read(self):
        output = BytesIO()
        ipk.write(
            output,
            test_package["epoch"],
            test_package["metadata"],
            test_package["scripts"],
            self.temp_dir.name,
        )

        output.seek(0)

        with ipk.Reader(output) as result:
            self.assertEqual(result.metadata, test_package["metadata"])
            self.assertEqual(result.scripts, test_package["scripts"])
            self.assertEqual(
                result.data.getnames(),
                ["."] + [member["path"] for member in test_package["data"]],
            )
