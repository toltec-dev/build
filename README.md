## toltecmk

[![toltecmk on PyPI](https://img.shields.io/pypi/v/toltecmk)](https://pypi.org/project/toltecmk)
![Status of the main branch](https://github.com/toltec-dev/build/actions/workflows/checks.yml/badge.svg)

`toltecmk` is a Python tool used to build software packages for the [Toltec repository](https://github.com/toltec-dev/toltec) from _[PKGBUILD](https://wiki.archlinux.org/index.php/PKGBUILD)-like build recipes_.
It automates common tasks such as fetching sources, building artifacts in a reproducible environment, and creating [Opkg-compatible archives](docs/ipk.md).

**Disclaimer: This is beta-quality software. The recipe format may change at any time in future releases. If you use `toltecmk` in other projects, it is advised to pin to a specific version.**

<p align="center">
    <img src="https://github.com/toltec-dev/build/raw/main/media/overview.svg" alt="toltecmk input: recipe; output: packages. Fetches sources based on instructions in the recipe." title="Overview of toltecmk">
</p>

### Setup

`toltecmk` is available as a Python package on PyPI.

```sh
pip install toltecmk
```

There are a few system requirements to use this tool:

* Linux-based operating system
* Python ⩾ 3.11
* Docker

### Basic Usage

To build a recipe located in the current directory, simply run:

```sh
toltecmk
```

This will process the recipe in a subfolder called `build` (which can be adjusted using the `--work-dir` flag) and generate packages in a subfolder called `dist` (`--dist-dir` flag).

### Documentation

* Tutorials and resources
    - [Guide to writing recipes](docs/writing-recipes.md)
    - [About ipk packages](docs/ipk.md)
* Reference
    - [Recipe format reference](docs/recipe-format.md)
    - [Details on the build process](docs/build-process.md)

### Related Projects

Many other build tools exist today for creating software packages, each major distribution having invented its own recipe and package formats.
Some important ones are listed below.
`toltecmk` itself uses an Arch Linux-style recipe format to build Debian-style packages.

<table>
    <tr>
        <th>Name</th>
        <th>Used by</th>
        <th>Recipe format</th>
        <th>Package format</th>
    </tr>
    <tr>
        <td colspan="4" align="center"><em>Debian-style</em></th>
    </tr>
    <tr>
        <td><a href="https://salsa.debian.org/debian/debhelper">debhelper</a></td>
        <td><a href="https://www.debian.org/">Debian</a>, <a href="https://ubuntu.com">Ubuntu</a>, and <a href="https://en.wikipedia.org/wiki/List_of_Linux_distributions#DEB-based">others</a></td>
        <td><a href="https://www.debian.org/doc/manuals/debmake-doc/ch05.en.html">Source packages</a> (Makefiles)</td>
        <td><a href="https://man7.org/linux/man-pages/man5/deb.5.html">deb</a></td>
    </tr>
    <tr>
        <td><a href="https://openwrt.org/docs/guide-developer/using_the_sdk">OpenWrt SDK</a></td>
        <td><a href="https://openwrt.org/">OpenWrt</a>, <a href="https://entware.net/">Entware</a></td>
        <td><a href="https://openwrt.org/docs/guide-developer/package-policies">Source packages</a> (Makefiles)</td>
        <td><a href="docs/ipk.md">ipk</a></td>
    </tr>
    <tr>
        <td colspan="4" align="center"><em>Fedora-style</em></td>
    </tr>
    <tr>
        <td><a href="https://github.com/rpm-software-management/rpm">rpmbuild</a></td>
        <td><a href="https://getfedora.org/">Fedora</a>, <a href="https://www.opensuse.org/">openSUSE</a>, and <a href="https://en.wikipedia.org/wiki/List_of_Linux_distributions#RPM-based">others</a></td>
        <td><a href="https://rpm-packaging-guide.github.io/#what-is-a-spec-file">spec</a> (DSL)</td>
        <td><a href="https://rpm.org/devel_doc/file_format.html">rpm</a></td>
    </tr>
    <tr>
        <td colspan="4" align="center"><em>Arch Linux-style</em></td>
    </tr>
    <tr>
        <td><a href="https://wiki.archlinux.org/title/Makepkg">makepkg</a></td>
        <td><a href="https://archlinux.org/">Arch Linux</a> and <a href="https://en.wikipedia.org/wiki/List_of_Linux_distributions#Pacman-based">others</a></td>
        <td><a href="https://wiki.archlinux.org/index.php/PKGBUILD">PKGBUILD</a> (Bash scripts)</td>
        <td>pkg.tar.zst</td>
    </tr>
    <tr>
        <td><a href="https://gitlab.alpinelinux.org/alpine/abuild">abuild</a></td>
        <td><a href="https://alpinelinux.org/">Alpine Linux</a></td>
        <td><a href="https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package#Getting_some_help">APKBUILD</a> (Bash scripts)</td>
        <td><a href="https://wiki.alpinelinux.org/wiki/Alpine_package_format">apk</a></td>
    </tr>
    <tr>
        <td colspan="4" align="center"><em>Others</em></td>
    </tr>
    <tr>
        <td><a href="https://nixos.org/manual/nix/unstable/command-ref/nix-build.html">nix-build</a></td>
        <td><a href="https://nixos.org/">NixOS</a></td>
        <td><a href="https://nixos.org/manual/nix/stable/#chap-writing-nix-expressions">Expressions</a> (DSL)</td>
        <td><a href="https://gist.github.com/jbeda/5c79d2b1434f0018d693">nar</a></td>
    </tr>
    <tr>
        <td><a href="https://dev.gentoo.org/~zmedico/portage/doc/man/ebuild.1.html">ebuild</a></td>
        <td><a href="https://www.gentoo.org/">Gentoo</a></td>
        <td><a href="https://wiki.gentoo.org/wiki/Ebuild">ebuild</a> (Bash scripts)</td>
        <td><a href="https://wiki.gentoo.org/wiki/Binary_package_guide#Understanding_the_binary_package_format">tbz2</a></td>
    </tr>
</table>
