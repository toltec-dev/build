# Copyright (c) 2021 The Toltec Contributors
# SPDX-License-Identifier: MIT
"""Read and write ipk packages."""

from gzip import GzipFile
from typing import Dict, IO, Optional, Type, Union
from types import TracebackType
from io import BytesIO
import tarfile
import operator
import os


def _targz_open(fileobj: IO[bytes], epoch: int) -> tarfile.TarFile:
    """Open a gzip compressed tar archive for writing."""
    # HACK: Modified code from `tarfile.TarFile.gzopen` to support
    # setting the `mtime` attribute on `GzipFile`
    gzipobj = GzipFile(
        filename="", mode="wb", compresslevel=9, fileobj=fileobj, mtime=epoch
    )

    try:
        # pylint:disable=consider-using-with
        archive = tarfile.TarFile(
            mode="w",
            fileobj=gzipobj,  # type:ignore
            format=tarfile.GNU_FORMAT,
        )
    except:
        gzipobj.close()
        raise

    archive._extfileobj = False  # type:ignore # pylint:disable=protected-access
    return archive


def _clean_info(
    root: Optional[str], epoch: int, info: tarfile.TarInfo
) -> tarfile.TarInfo:
    """
    Remove variable data from an archive entry.

    :param root: absolute path to the root directory from which the
        entry was added, or None to disable turning the name into a
        relative path
    :param epoch: fixed modification time to set
    :param info: tarinfo object to set
    :returns: changed tarinfo
    """
    if root is not None:
        info.name = os.path.relpath("/" + info.name, root)

    if not info.name.startswith("."):
        info.name = "./" + info.name

    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = epoch

    return info


def _add_file(
    archive: tarfile.TarFile, name: str, mode: int, epoch: int, data: bytes
) -> None:
    """
    Add an in-memory file into a tar archive.

    :param archive: archive to append to
    :param name: name of the file to add
    :param mode: permissions of the file
    :param epoch: fixed modification time to set
    :param data: file contents
    """
    info = tarfile.TarInfo("./" + name)
    info.size = len(data)
    info.mode = mode
    archive.addfile(_clean_info(None, epoch, info), BytesIO(data))


def write_control(
    file: IO[bytes], epoch: int, metadata: str, scripts: Dict[str, str]
) -> None:
    """
    Create the control sub-archive of an ipk package.

    See <https://www.debian.org/doc/debian-policy/ch-controlfields.html>
    and <https://www.debian.org/doc/debian-policy/ch-maintainerscripts.html>.

    :param file: file to which the sub-archive will be written
    :param epoch: fixed modification time to set in the archive metadata
    :param metadata: package metadata (main control file)
    :param scripts: optional maintainer scripts
    """
    with _targz_open(file, epoch) as archive:
        root_info = tarfile.TarInfo("./")
        root_info.type = tarfile.DIRTYPE
        root_info.mode = 0o755
        archive.addfile(_clean_info(None, epoch, root_info))

        _add_file(archive, "control", 0o644, epoch, metadata.encode())

        for name, script in sorted(scripts.items(), key=operator.itemgetter(0)):
            _add_file(archive, name, 0o755, epoch, script.encode())


def write_data(
    file: IO[bytes],
    epoch: int,
    pkg_dir: Optional[str] = None,
) -> None:
    """
    Create the data sub-archive of an ipk package.

    :param file: file to which the sub-archive will be written
    :param epoch: fixed modification time to set in the archive metadata
    :param pkg_dir: directory containing the package tree to include in the
        data sub-archive, leave empty to generate an empty data archive
    """
    with _targz_open(file, epoch) as archive:
        if pkg_dir is not None:
            archive.add(
                pkg_dir, filter=lambda info: _clean_info(pkg_dir, epoch, info)
            )


def write(
    file: IO[bytes],
    epoch: int,
    metadata: str,
    scripts: Dict[str, str],
    pkg_dir: Optional[str] = None,
) -> None:
    """
    Create an ipk package.

    :param file: file to which the package will be written
    :param epoch: fixed modification time to set in the archives metadata
    :param metadata: package metadata (main control file)
    :param scripts: optional maintainer scripts
    :param pkg_dir: directory containing the package tree to include in the
        data sub-archive, leave empty to generate an empty data archive
    """
    with BytesIO() as control, BytesIO() as data, _targz_open(
        file, epoch
    ) as archive:
        root_info = tarfile.TarInfo("./")
        root_info.type = tarfile.DIRTYPE
        archive.addfile(_clean_info(None, epoch, root_info))

        write_control(control, epoch, metadata, scripts)
        _add_file(archive, "control.tar.gz", 0o644, epoch, control.getvalue())

        write_data(data, epoch, pkg_dir)
        _add_file(archive, "data.tar.gz", 0o644, epoch, data.getvalue())

        _add_file(archive, "debian-binary", 0o644, epoch, b"2.0\n")


class Reader:
    """Read from ipk packages."""

    def __init__(self, file: Union[str, IO[bytes]]):
        """
        Create a package reader.
        :param file: path to the package file to read, or opened
            file object for a package file (in the second case, the
            package file object will not by closed on exit)
        """
        self._file: Optional[IO[bytes]] = None

        if isinstance(file, str):
            self._file = open(file, "rb")  # pylint:disable=consider-using-with
            self._close = True
        else:
            self._file = file
            self._close = False

        self._root_archive: Optional[tarfile.TarFile] = None
        self._data_file: Optional[IO[bytes]] = None

        self.data: Optional[tarfile.TarFile] = None
        self.metadata: Optional[str] = None
        self.scripts: Dict[str, str] = {}

    def __enter__(self) -> "Reader":
        """Load package data to memory."""
        root_archive = tarfile.TarFile.open(fileobj=self._file)
        control_file = root_archive.extractfile("./control.tar.gz")
        assert control_file is not None

        with control_file:
            with tarfile.TarFile.open(fileobj=control_file) as control_archive:
                for member in control_archive.getmembers():
                    if member.isfile():
                        file = control_archive.extractfile(member)
                        assert file is not None
                        with file:
                            contents = file.read().decode("utf-8")
                            if member.name == "./control":
                                self.metadata = contents
                            else:
                                self.scripts[member.name[2:]] = contents

        data_file = root_archive.extractfile("./data.tar.gz")
        assert data_file is not None
        self._root_archive = root_archive
        self._data_file = data_file
        self.data = tarfile.TarFile.open(fileobj=data_file)

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_inst: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Free resources containing package data."""
        if self.data is not None:
            self.data.close()
            self.data = None

        if self._data_file is not None:
            self._data_file.close()
            self._data_file = None

        if self._root_archive is not None:
            self._root_archive.close()
            self._root_archive = None

        if self._file is not None:
            if self._close:
                self._file.close()

            self._file = None
