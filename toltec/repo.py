# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""
Repository management.
"""

import gzip
import locale
import logging
import os
import textwrap
from .util import file_sha256
from . import ipk

logger = logging.getLogger(__name__)


def make_index(base_dir: str, _start: bool = True) -> None:
    """
    Recursively generate index files for all the packages in folder.

    Traverses :param:`base_dir` and all its subfolders and creates a package
    index for each subfolder containing the metadata of ipk packages
    contained directly in that folder.

    :param base_dir: directory to start the traversal from
    """
    if _start:
        logger.info("Generating package index")

    index_path = os.path.join(base_dir, "Packages")
    index_gzip_path = os.path.join(base_dir, "Packages.gz")

    with open(
        index_path, "w", encoding=locale.getencoding()
    ) as index_file, gzip.open(index_gzip_path, "wt") as index_gzip_file:
        for entry in os.scandir(base_dir):
            if entry.name in ("Packages", "Packages.gz"):
                pass
            elif entry.is_dir():
                make_index(entry.path, _start=False)
            elif entry.is_file() and entry.name.endswith(".ipk"):
                with ipk.Reader(entry.path) as package:
                    metadata = package.metadata
                    assert metadata is not None

                metadata += textwrap.dedent(
                    f"""\
                    Filename: {entry.name}
                    SHA256sum: {file_sha256(entry.path)}
                    Size: {os.path.getsize(entry.path)}

                    """
                )

                index_file.write(metadata)
                index_gzip_file.write(metadata)
